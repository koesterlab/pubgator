from pubgator import PubGator, ExportFormat


class TestExportPublications:
    def test_export_biocxml(self, client: PubGator):
        result = client.export_publications(pmids=[36543932], format=ExportFormat.BIOC)
        assert result.documents[0].id == "36543932"

    def test_export_biocjson(self, client: PubGator):
        result = client.export_publications(pmids=[29355051], format=ExportFormat.JSON)
        assert result[0]["id"] == "29355051"

    def test_export_pubtator(self, client: PubGator):
        result = client.export_publications(
            pmids=[29355051], format=ExportFormat.PUBTATOR
        )

        assert "29355051" in result
