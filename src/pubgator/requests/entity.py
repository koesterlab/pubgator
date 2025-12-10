from typing import Optional
from urllib.parse import urlencode

from ..models import BioConcept


class EntityRequest:
    """Builder for entity-related requests."""

    @staticmethod
    def build_url(
        base_url: str,
        query: str,
        concept: Optional[BioConcept] = None,
        limit: Optional[int] = None,
    ) -> str:
        """Build URL for entity autocomplete/ID lookup.

        Args:
            base_url: Base API URL
            query: Free text query
            concept: Optional bioconcept type to filter by
            limit: Optional limit on number of results

        Returns:
            Complete API URL
        """
        url = f"{base_url}/entity/autocomplete/"
        params = {"query": query}

        if concept:
            params["concept"] = concept.value
        if limit:
            params["limit"] = str(limit)

        return f"{url}?{urlencode(params)}"
