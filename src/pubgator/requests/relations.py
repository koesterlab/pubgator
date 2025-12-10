from typing import Optional
from urllib.parse import urlencode

from ..models import BioConcept, RelationType


class RelationRequest:
    """Builder for relation lookup requests."""

    @staticmethod
    def build_url(
        base_url: str,
        entity1: str,
        relation_type: Optional[RelationType] = None,
        entity2_type: Optional[BioConcept] = None,
    ) -> str:
        """Build URL for finding related entities.

        Args:
            base_url: Base API URL
            entity1: First entity ID
            relation_type: Optional relation type filter
            entity2_type: Optional entity type filter for second entity

        Returns:
            Complete API URL
        """
        url = f"{base_url}/relations"
        params = {"e1": entity1}

        if relation_type:
            params["type"] = relation_type.value
        if entity2_type:
            params["e2"] = entity2_type.value

        return f"{url}?{urlencode(params)}"
