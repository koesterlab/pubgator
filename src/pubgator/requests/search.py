from typing import Optional
from urllib.parse import urlencode


class SearchRequest:
    """Builder for search requests."""

    @staticmethod
    def build_url(base_url: str, text: str, page: Optional[int] = None) -> str:
        """Build URL for text/entity/relation search.

        Args:
            base_url: Base API URL
            text: Search query (can be free text, entity ID, or relation query)
            page: Optional page number for pagination

        Returns:
            Complete API URL
        """
        url = f"{base_url}/search/"
        params = {"text": text}

        if page:
            params["page"] = str(page)

        return f"{url}?{urlencode(params)}"
