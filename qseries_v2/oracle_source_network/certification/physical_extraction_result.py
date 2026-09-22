
from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class PhysicalExtractionResult:
    league: str
    source_bytes: int
    events: int
    status: str
    unique_ids: int
    read_only: bool
    execution_authority: bool = False

def classify(league,body,events):
    ids=[x.canonical_event_id for x in events]
    if events:
        status="EXTRACTING"
    else:
        low=body.lower()
        hints=any(x in low for x in ("eventid","gameid","matchid","hometeam","awayteam","home_team","away_team","fixtures","schedule","score"))
        status="UNSUPPORTED_STRUCTURE" if hints else "NO_CURRENT_EVENTS_OR_NO_STRUCTURED_EVENT_DATA"
    return PhysicalExtractionResult(
        league=league,
        source_bytes=len(body.encode("utf-8",errors="ignore")),
        events=len(events),
        status=status,
        unique_ids=len(set(ids)),
        read_only=all(getattr(x,"read_only",False) is True for x in events),
    )
