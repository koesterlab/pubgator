"""Request builders for different PubTator3 API endpoints."""

from urllib.parse import urlencode

from ..models import ExportFormat


class ExportRequest:
    """Builder for publication export requests."""

    @staticmethod
    def build_url(
        base_url: str, format: ExportFormat, pmids: list[int], full: bool = False
    ) -> str:
        """Build URL for exporting publications by PMIDs.

        Args:
            base_url: Base API URL
            format: Export format (pubtator, biocxml, biocjson)
            pmids: List of PubMed IDs
            full: Whether to include full text (only for biocxml/biocjson)

        Returns:
            Complete API URL
        """
        pmids_str = ",".join([str(pmid) for pmid in pmids])
        match format:
            case ExportFormat.BIOC:
                query_format = "biocxml"
            case ExportFormat.JSON:
                query_format = "biocjson"
            case ExportFormat.PUBTATOR:
                query_format = "pubtator"
        url = f"{base_url}/publications/export/{query_format}"
        params = {"pmids": pmids_str}

        if full and format != ExportFormat.PUBTATOR:
            params["full"] = "true"

        return f"{url}?{urlencode(params)}"

    @staticmethod
    def build_pmc_url(base_url: str, format: ExportFormat, pmcids: list[str]) -> str:
        """Build URL for exporting publications by PMC IDs.

        Args:
            base_url: Base API URL
            format: Export format (biocxml or biocjson only)
            pmcids: List of PMC IDs

        Returns:
            Complete API URL
        """
        pmcids_str = ",".join(pmcids)
        url = f"{base_url}/publications/pmc_export/{format.value}"
        params = {"pmcids": pmcids_str}

        return f"{url}?{urlencode(params)}"
