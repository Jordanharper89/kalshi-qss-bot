
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True, slots=True)
class SourceHealth:
    provider: str
    age_seconds: float
    fresh: bool
    payload_present: bool
    execution_authority: bool = False

def _parse_iso(s):
    return datetime.fromisoformat(str(s).replace("Z","+00:00"))

def evaluate(snapshot, now_iso=None, max_age_seconds=120.0):
    now = _parse_iso(now_iso) if now_iso else datetime.now(timezone.utc)
    observed = _parse_iso(snapshot["observed_at"])
    age = max(0.0, (now-observed).total_seconds())
    payload_present = bool(snapshot.get("payload_sha256")) and len(snapshot["payload_sha256"]) == 64
    return SourceHealth(
        provider=str(snapshot["provider"]),
        age_seconds=age,
        fresh=payload_present and age <= float(max_age_seconds),
        payload_present=payload_present,
        execution_authority=False,
    )
