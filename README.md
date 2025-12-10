# PubGator 🐊

A lightweight python wrapper for the [PubTator3 API](https://www.ncbi.nlm.nih.gov/research/pubtator3/).
PubGator allows to easily interact with the PubTator API.
It provides a simple interface to search for publications, retrieve full annotations, and find entities and relations.
It also automatically handles pagination and rate limiting.

## Usage

```python
from pubgator import PubGator, ExportFormat, BioConcept

# Initialize the PubGator client
pg = PubGator()

# Search for publications containing the chemical remdesivir
publications = pg.search("@CHEMICAL_remdesivir", max_ret=100)
pmids = [publication.pmid for publication in publications]

# Retrieve full annotations for the set of publications
annotations = pg.export_publications(pmids=pmids, format=ExportFormat.BIOC)

# Find entities
entities = pg.autocomplete("cancer", concept=BioConcept.DISEASE)
```

## License

[MIT License](LICENSE)

## Authors

- [Felix Wiegand](https://github.com/fxwiegand)
