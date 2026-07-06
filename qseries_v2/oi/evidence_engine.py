from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Evidence:
    source: str
    category: str
    value: dict
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

class EvidenceEngine:
    def __init__(self):
        self._items=[]

    def add(self,evidence):
        self._items.append(evidence)

    def all(self):
        return list(self._items)

evidence_engine = EvidenceEngine()
