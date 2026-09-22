from dataclasses import dataclass, asdict
from typing import Optional, Mapping, Any
import hashlib, re

REVISION = "OSN_002_VENUE_NEUTRAL_SPORTS_EVENT_IDENTITY_OBSERVATION_CONTRACT_V1"
EXECUTION_AUTHORITY = False

def _norm(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (v or "").strip().lower()).strip("-")

def canonical_event_id(sport: str, league: str, season: str, home: str, away: str, scheduled_start: str) -> str:
    raw = "|".join((_norm(sport), _norm(league), _norm(season), _norm(home), _norm(away), scheduled_start.strip()))
    return "osn:sport:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

@dataclass(frozen=True)
class SportsEventIdentity:
    sport: str
    league: str
    season: str
    home: str
    away: str
    scheduled_start: str

    @property
    def event_id(self) -> str:
        return canonical_event_id(self.sport,self.league,self.season,self.home,self.away,self.scheduled_start)

@dataclass(frozen=True)
class SportsObservation:
    identity: SportsEventIdentity
    provider: str
    provider_event_id: str
    observed_at: str
    status: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    payload_sha256: str = ""
    provenance_uri: str = ""
    source_authority: str = "official"
    execution_authority: bool = False

    def as_dict(self) -> Mapping[str, Any]:
        d = asdict(self)
        d["event_id"] = self.identity.event_id
        return d
