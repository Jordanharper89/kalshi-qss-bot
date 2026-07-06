from dataclasses import dataclass, asdict
from datetime import datetime, timezone

@dataclass
class Play:
    ticker: str
    title: str
    category: str = "UNKNOWN"
    play_type: str = "VALUE"
    mission: str = "WATCH"
    side: str = "WATCH"
    current_price: float = 0.0
    fair_value: float = 0.0
    edge: float = 0.0
    confidence: float = 0.0
    grade: str = "UNRATED"
    source: str = "ORACLE"
    reason: str = ""

    def to_dict(self):
        d = asdict(self)
        d["timestamp"] = datetime.now(timezone.utc).isoformat()
        return d
