"""Data models for PubGator."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any, Dict


class ExportFormat(str, Enum):
    """Supported export formats for publications."""

    PUBTATOR = "pubtator"
    BIOC = "bioc"
    JSON = "json"


class BioConcept(str, Enum):
    """Supported bioconcept types."""

    GENE = "gene"
    DISEASE = "disease"
    CHEMICAL = "chemical"
    VARIANT = "variant"
    SPECIES = "species"
    CELL_LINE = "cell_line"


class RelationType(str, Enum):
    """Supported relation types between entities."""

    TREAT = "treat"
    CAUSE = "cause"
    COTREAT = "cotreat"
    CONVERT = "convert"
    COMPARE = "compare"
    INTERACT = "interact"
    ASSOCIATE = "associate"
    POSITIVE_CORRELATE = "positive_correlate"
    NEGATIVE_CORRELATE = "negative_correlate"
    PREVENT = "prevent"
    INHIBIT = "inhibit"
    STIMULATE = "stimulate"
    DRUG_INTERACT = "drug_interact"
    ANY = "ANY"


@dataclass
class Entity:
    """Represents a bioconcept entity."""

    id: str
    type: str
    text: str
    score: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Relation:
    """Represents a relation between two entities."""

    type: RelationType
    source: str
    target: str
    publications: int

    @classmethod
    def from_json(cls, data: dict) -> "Relation":
        return cls(
            type=RelationType(data["type"]),
            source=data["source"],
            target=data["target"],
            publications=data["publications"],
        )


@dataclass
class Publication:
    """Represents a publication with annotations."""

    pmid: int
    title: str
    journal: str
    doi: str
    score: float
    authors: list[str]
    pmcid: Optional[str] = None
    date: Optional[str] = None
    meta_date_publication: Optional[str] = None
    meta_volume: Optional[str] = None
    meta_issue: Optional[str] = None
    meta_pages: Optional[str] = None
    text_hl: Optional[str] = None
    citations: Optional[Dict] = None

    def __hash__(self):
        return hash(self.pmid)

    def __eq__(self, other):
        if isinstance(other, Publication):
            return self.pmid == other.pmid
        return False

    @classmethod
    def from_json(cls, data: dict) -> "Publication":
        return cls(
            pmid=int(data.get("pmid", 0)),
            pmcid=data.get("pmcid", None),
            title=data.get("title", ""),
            journal=data.get("journal", ""),
            doi=data.get("doi", ""),
            score=float(data.get("score", 0)),
            authors=data.get("authors", []),
            date=data.get("date", None),
            meta_date_publication=data.get("meta_date_publication"),
            meta_volume=data.get("meta_volume"),
            meta_issue=data.get("meta_issue"),
            meta_pages=data.get("meta_pages"),
            text_hl=data.get("text_hl"),
            citations=data.get("citations"),
        )


@dataclass
class SearchResult:
    """Represents search results from PubTator3."""

    query: str
    total_results: int
    publications: list[Publication] = field(default_factory=list)
    page: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AutocompleteResult:
    """Represents an autocomplete suggestion result."""

    db_id: str
    db: str
    name: str
    type: BioConcept
    description: Optional[str]
    match: str
