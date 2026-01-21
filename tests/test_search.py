from pubgator import PubGator


class TestSearch:
    def test_search_entity(self, client: PubGator):
        results = client.search("@CHEMICAL_remdesivir", max_ret=25)

        assert len(results) == 25
        first_result = results[0]
        assert first_result.score > 100

    def test_search_with_sections(self, client: PubGator):
        results = client.search("CHEMICAL_remdesivir", sections=["title"], max_ret=25)
        for r in results:
            assert "remdesivir" in r.title.lower()
