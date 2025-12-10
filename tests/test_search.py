from pubgator import PubGator


class TestSearch:
    def test_search_entity(self, client: PubGator):
        results = client.search("@CHEMICAL_remdesivir", max_ret=25)

        assert len(results) == 25
        first_result = results[0]
        assert first_result.score > 100
