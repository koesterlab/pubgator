import time
from typing import Optional, Any, List
from bioc import biocxml
import httpx

from .models import (
    ExportFormat,
    BioConcept,
    Relation,
    AutocompleteResult,
    Publication,
    RelationType,
)

from .requests.export import ExportRequest
from .requests.entity import EntityRequest
from .requests.search import SearchRequest
from .requests.relations import RelationRequest


class PubGator:
    """Main client for interacting with PubTator3 API.

    This client provides a modern, typed interface to the PubTator3 API
    with automatic rate limiting to comply with the 3 requests/second limit.

    Example:
        >>> client = PubGator()
        >>> results = client.search("@CHEMICAL_remdesivir")
        >>> entities = client.autocomplete("remdesivir", concept=BioConcept.CHEMICAL)
    """

    DEFAULT_BASE_URL = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api"
    TIME_EPSILON = 1e-4

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 10.0,
        rate_limit: bool = True,
        max_requests_per_second: int = 3,
    ):
        """Initialize PubGator client.

        Args:
            base_url: Base URL for PubTator3 API
            timeout: Request timeout in seconds
            rate_limit: Whether to enforce rate limiting
            max_requests_per_second: Maximum number of requests per second (default: 3)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.rate_limit = rate_limit
        self._last_request_time = 0.0
        self._request_interval = 1.0 / max_requests_per_second if rate_limit else 0.0

        self.client = httpx.Client(timeout=timeout)

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting by sleeping if necessary."""
        if not self.rate_limit:
            return

        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self._request_interval:
            time.sleep(self._request_interval - time_since_last + self.TIME_EPSILON)

        self._last_request_time = time.time()

    def _make_request(self, url: str, retries: int = 3) -> httpx.Response:
        """Make HTTP request with retry logic and exponential backoff.

        Args:
            url: Complete URL to request
            retries: Maximum number of retry attempts

        Returns:
            HTTP response

        Raises:
            httpx.HTTPError: If request fails after all retries
        """
        for attempt in range(retries):
            try:
                self._enforce_rate_limit()
                response = self.client.get(url)

                if response.status_code == 429:
                    time.sleep(int(response.headers.get("Retry-After", 3)))
                    continue

                response.raise_for_status()
                return response

            except (
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.RemoteProtocolError,
            ):
                if attempt == retries - 1:
                    raise
                time.sleep(2**attempt)

            except httpx.HTTPStatusError as e:
                if e.response.status_code < 500:
                    raise
                if attempt == retries - 1:
                    raise
                time.sleep(2**attempt)

        raise httpx.HTTPError(f"Failed after {retries} attempts")

    def export_publications(
        self,
        pmids: list[int],
        format: ExportFormat = ExportFormat.BIOC,
        full: bool = False,
        retries: int = 3,
    ) -> Any:
        """Export annotations for publications by PMID.

        Args:
            pmids: List of PubMed IDs
            format: Export format (pubtator, biocxml, biocjson)
            full: Whether to include full text (only for biocxml/biocjson)
            retries: Maximum number of retry attempts

        Returns:
            Exported data as string (pubtator/biocxml) or dict (biocjson)

        Example:
            >>> client.export_publications(["29355051"], format=ExportFormat.BIOCJSON)
        """
        url = ExportRequest.build_url(self.base_url, format, pmids, full)
        response = self._make_request(url, retries)

        return self._export_results(response, format)

    def export_pmc_publications(
        self,
        pmcids: list[str],
        format: ExportFormat = ExportFormat.BIOC,
        retries: int = 3,
    ) -> Any:
        """Export full-text publications by PMC ID.

        Args:
            pmcids: List of PMC IDs (e.g., ['PMC7696669'])
            format: Export format (biocxml or biocjson only)
            retries: Maximum number of retry attempts

        Returns:
            Exported data as string (biocxml) or dict (biocjson)

        Example:
            >>> client.export_pmc_publications(["PMC7696669", "PMC8869656"])
        """
        if format == ExportFormat.PUBTATOR:
            raise ValueError("PMC export does not support pubtator format")

        url = ExportRequest.build_pmc_url(self.base_url, format, pmcids)
        response = self._make_request(url, retries)

        return self._export_results(response, format)

    def _export_results(self, response, format: ExportFormat) -> Any:
        match format:
            case ExportFormat.BIOC:
                return biocxml.loads(response.text)
            case ExportFormat.JSON:
                return response.json()["PubTator3"]
            case ExportFormat.PUBTATOR:
                return response.text

    def autocomplete(
        self,
        query: str,
        concept: Optional[BioConcept] = None,
        limit: Optional[int] = None,
        retries: int = 3,
    ) -> list[AutocompleteResult]:
        """Find entity IDs through autocomplete.

        Args:
            query: Free text search query
            concept: Optional bioconcept type to filter by
            limit: Maximum number of results to return
            retries: Maximum number of retry attempts

        Returns:
            List of autocomplete results with entity IDs

        Example:
            >>> results = client.autocomplete("remdesivir", concept=BioConcept.CHEMICAL)
            >>> for entity in results:
            >>>     print(entity.name)
            >>>     print(entity.description)
        """
        url = EntityRequest.build_url(self.base_url, query, concept, limit)
        response = self._make_request(url, retries)
        data = response.json()

        results = []
        for item in data:
            results.append(
                AutocompleteResult(
                    db_id=item.get("db_id", ""),
                    db=item.get("db", ""),
                    name=item.get("name", ""),
                    type=item.get("type", ""),
                    description=item.get("description", None),
                    match=item.get("match", ""),
                )
            )

        return results

    def search(
        self,
        query: str,
        sections: Optional[List[str]] = None,
        max_ret: int = 100,
        retries: int = 3,
    ) -> list[Publication]:
        """Search PubTator3 for publications.

        Supports free text, entity IDs, boolean queries, and relation queries.

        Args:
            query: Search query (text, entity ID, or relation query)
            sections: List of sections to search in. Defaults to None. This means all sections will be used. Available sections are: 'title', 'abstract', 'conclusion', 'discussion', 'results', 'methods', and 'introduction'
            max_ret: Maximum number of results to return. Defaults to 100. Paging is automatically handled by PubGator.
            retries: Maximum number of retry attempts

        Returns:
            Search results as dictionary

        Examples:
            >>> # Free text search
            >>> client.search("breast cancer")

            >>> # Entity search
            >>> client.search("@CHEMICAL_remdesivir")

            >>> # Boolean search
            >>> client.search("@DISEASE_COVID_19 AND @GENE_PON1")

            >>> # Relation search
            >>> client.search("relations:treat|@CHEMICAL_Doxorubicin|@DISEASE_Neoplasms")
        """
        url = SearchRequest.build_url(self.base_url, query, sections)
        response = self._make_request(url, retries).json()
        total_pages = min(response["total_pages"], max_ret // 10 + 1)
        results = response["results"]
        for page in range(2, total_pages + 1):
            url = SearchRequest.build_url(self.base_url, query, sections, page)
            response = self._make_request(url, retries).json()
            results.extend(response["results"])
        results = results[:max_ret]
        publications = [Publication.from_json(pub) for pub in results]
        return publications

    def search_relations(
        self,
        e1: str,
        type: Optional[RelationType] = None,
        e2: Optional[BioConcept] = None,
        retries: int = 3,
    ) -> list[Relation]:
        """Search for specific relations between two entities.

        Args:
            entity1: First entity ID
            relation_type: Type of relation (e.g., RelationType.NEGATIVE_CORRELATE)
            entity2: Second entity ID or entity type
            retries: Maximum number of retry attempts

        Returns:
            Search results as list of Relation objects

        Example:
            >>> # Search for treatment relations between a drug and disease
            >>> client.search_relation(
            ...     RelationType.TREAT,
            ...     "@CHEMICAL_Doxorubicin",
            ...     BioConcept.DISEASE
            ... )

            >>> # Search for any gene associations with a disease
            >>> client.search_relation(
            ...     RelationType.ASSOCIATE,
            ...     "@DISEASE_COVID_19",
            ...     BioConcept.GENE
            ... )
        """
        query = RelationRequest.build_url(self.base_url, e1, type, e2)
        response = self._make_request(query, retries)
        relations = [Relation.from_json(rel) for rel in response.json()]
        return relations

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def close(self):
        """Close the HTTP client."""
        self.client.close()
