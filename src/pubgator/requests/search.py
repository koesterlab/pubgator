from typing import Optional, List
from urllib.parse import urlencode


class SearchRequest:
    """Builder for search requests."""

    @staticmethod
    def build_url(
        base_url: str,
        text: str,
        sections: Optional[List[str]] = None,
        page: Optional[int] = None,
    ) -> str:
        """Build URL for text/entity/relation search.

        Args:
            base_url: Base API URL
            text: Search query (can be free text, entity ID, or relation query)
            sections: Optional sections to search in (e.g., 'title', 'abstract', ...)
            page: Optional page number for pagination

        Returns:
            Complete API URL
        """
        url = f"{base_url}/search/"
        params = {"text": text}

        if sections:
            params["sections"] = ",".join(sections)

        if page:
            params["page"] = str(page)

        return f"{url}?{urlencode(params)}"
