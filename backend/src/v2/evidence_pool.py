from dataclasses import dataclass, field


@dataclass
class EvidenceItem:
    id: str
    claim: str
    source: str = ""
    url: str = ""
    relevance: float = 0.0
    reliability: float = 0.0
    freshness: float = 0.0
    coverage: float = 0.0
    contradiction: float = 0.0
    redundancy: float = 0.0
    metadata: dict = field(default_factory=dict)


class EvidencePool:
    def __init__(self):
        self.items = []

    def add(self, item):
        if isinstance(item, EvidenceItem):
            self.items.append(item)

    def add_many(self, items):
        for item in items:
            self.add(item)

    def to_dict(self):
        return [item.__dict__.copy() for item in self.items]

    def __len__(self):
        return len(self.items)
