from pubgator import PubGator, BioConcept, RelationType, Relation


class TestRelations:
    def test_find_related_entities_basic(self, client: PubGator):
        """Test finding entities related to a given entity.

        API Example: Pass entityId to e1 parameter to find related entities.
        This uses the "Find Related Entities" endpoint.
        """
        results = client.search_relations(
            "@DISEASE_Alzheimer_Disease", RelationType.TREAT, BioConcept.CHEMICAL
        )

        assert isinstance(results, list)
        assert len(results) > 0
        for relation in results:
            assert isinstance(relation, Relation)
            assert relation.type == RelationType.TREAT
