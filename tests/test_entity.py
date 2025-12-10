from pubgator import PubGator, BioConcept


class TestEntityAutocomplete:
    def test_autocomplete_basic_example(self, client: PubGator):
        results = client.autocomplete(
            "remdesivir", concept=BioConcept.CHEMICAL, limit=5
        )

        assert len(results) > 0
        assert any("remdesivir" in r.name.lower() for r in results)
        assert any("triphosphate" in r.name.lower() for r in results)
        assert any("monophosphate" in r.name.lower() for r in results)

    def test_autocomplete_with_description(self, client: PubGator):
        results = client.autocomplete("BRAF", concept=BioConcept.GENE, limit=1)

        assert len(results) == 1

        result = results[0]
        assert result.description is not None and result.description != ""
        assert result.name == "BRAF"
        assert result.db_id == "673"
        assert result.db == "ncbi_gene"
