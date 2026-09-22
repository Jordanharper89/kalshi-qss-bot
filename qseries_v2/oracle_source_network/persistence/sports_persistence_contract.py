
from dataclasses import dataclass
from hashlib import sha256
import json

@dataclass(frozen=True)
class SportsPersistenceObservation:
    source_id:str
    observed_at:str
    observation_type:str
    provider:str
    subject:str
    provenance_hash:str
    payload:dict
    source_class:str="official_sports_event"

def from_canonical_event(event):
    payload={
        "canonical_event_id":event.canonical_event_id,
        "league":event.league,
        "season":event.season,
        "home_team":event.home_team,
        "away_team":event.away_team,
        "scheduled_start":event.scheduled_start,
        "status":getattr(event,"status",None),
        "home_score":getattr(event,"home_score",None),
        "away_score":getattr(event,"away_score",None),
        "provider_event_id":getattr(event,"provider_event_id",None),
        "schedule_revision":getattr(event,"schedule_revision",0),
        "read_only":True,
        "execution_authority":False,
    }
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()
    ph=sha256(raw).hexdigest()
    return SportsPersistenceObservation(
        source_id=f"source.sports.{event.league.lower()}.{event.provider}.{event.canonical_event_id}",
        observed_at=event.source_observed_at,
        observation_type="official_sports_event",
        provider=event.provider,
        subject=event.canonical_event_id,
        provenance_hash=ph,
        payload=payload,
    )
