import time
from typing import Optional, Any
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
    MAX_REQUESTS_PER_SECOND = 3

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 10.0,
        rate_limit: bool = True,
    ):
        """Initialize PubGator client.

        Args:
            base_url: Base URL for PubTator3 API
            timeout: Request timeout in seconds
            rate_limit: Whether to enforce rate limiting (3 req/sec)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.rate_limit = rate_limit
        self._last_request_time = 0.0
        self._request_interval = (
            1.0 / self.MAX_REQUESTS_PER_SECOND if rate_limit else 0.0
        )

        self.client = httpx.Client(timeout=timeout)

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting by sleeping if necessary."""
        if not self.rate_limit:
            return

        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self._request_interval:
            time.sleep(self._request_interval - time_since_last)

        self._last_request_time = time.time()

    def _make_request(self, url: str) -> httpx.Response:
        """Make HTTP request with rate limiting.

        Args:
            url: Complete URL to request

        Returns:
            HTTP response

        Raises:
            httpx.HTTPError: If request fails
        """
        self._enforce_rate_limit()
        response = self.client.get(url)
        response.raise_for_status()
        return response

    def export_publications(
        self,
        pmids: list[int],
        format: ExportFormat = ExportFormat.BIOC,
        full: bool = False,
    ) -> Any:
        """Export annotations for publications by PMID.

        Args:
            pmids: List of PubMed IDs
            format: Export format (pubtator, biocxml, biocjson)
            full: Whether to include full text (only for biocxml/biocjson)

        Returns:
            Exported data as string (pubtator/biocxml) or dict (biocjson)

        Example:
            >>> client.export_publications(["29355051"], format=ExportFormat.BIOCJSON)
        """
        url = ExportRequest.build_url(self.base_url, format, pmids, full)
        response = self._make_request(url)

        return self._export_results(response, format)

    def export_pmc_publications(
        self, pmcids: list[str], format: ExportFormat = ExportFormat.BIOC
    ) -> Any:
        """Export full-text publications by PMC ID.

        Args:
            pmcids: List of PMC IDs (e.g., ['PMC7696669'])
            format: Export format (biocxml or biocjson only)

        Returns:
            Exported data as string (biocxml) or dict (biocjson)

        Example:
            >>> client.export_pmc_publications(["PMC7696669", "PMC8869656"])
        """
        if format == ExportFormat.PUBTATOR:
            raise ValueError("PMC export does not support pubtator format")

        url = ExportRequest.build_pmc_url(self.base_url, format, pmcids)
        response = self._make_request(url)

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
    ) -> list[AutocompleteResult]:
        """Find entity IDs through autocomplete.

        Args:
            query: Free text search query
            concept: Optional bioconcept type to filter by
            limit: Maximum number of results to return

        Returns:
            List of autocomplete results with entity IDs

        Example:
            >>> results = client.autocomplete("remdesivir", concept=BioConcept.CHEMICAL)
            >>> description = results[0].description
        """
        url = EntityRequest.build_url(self.base_url, query, concept, limit)
        response = self._make_request(url)
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

    def search(self, query: str, max_ret: int = 100) -> list[Publication]:
        """Search PubTator3 for publications.

        Supports free text, entity IDs, boolean queries, and relation queries.

        Args:
            query: Search query (text, entity ID, or relation query)
            max_ret: Maximum number of results to return. Defaults to 100. Paging is automatically handled by PubGator.

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
        url = SearchRequest.build_url(self.base_url, query)
        response = self._make_request(url).json()
        total_pages = min(response["total_pages"], max_ret // 10 + 1)
        results = response["results"]
        for page in range(2, total_pages + 1):
            url = SearchRequest.build_url(self.base_url, query, page)
            response = self._make_request(url).json()
            results.extend(response["results"])
        results = results[:max_ret]
        publications = [Publication.from_json(pub) for pub in results]
        return publications

    def search_relations(
        self,
        e1: str,
        type: Optional[RelationType] = None,
        e2: Optional[BioConcept] = None,
    ) -> list[Relation]:
        """Search for specific relations between two entities.

        Args:
            relation_type: Type of relation (e.g., RelationType.NEGATIVE_CORRELATE)
            entity1: First entity ID
            entity2: Second entity ID or entity type
            page: Page number for pagination

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
        response = self._make_request(query)
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
