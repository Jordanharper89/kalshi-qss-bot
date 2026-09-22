
from dataclasses import dataclass

from qseries_v2.oracle_source_network.mapping.football_event_extractor import extract_football_events
from qseries_v2.oracle_source_network.mapping.basketball_event_extractor import extract_basketball_events
from qseries_v2.oracle_source_network.mapping.hockey_soccer_event_extractor import extract_hockey_soccer_events

@dataclass(frozen=True, slots=True)
class ExtractionCertification:
    category: str
    events: int
    unique_ids: int
    stable_identity: bool
    read_only: bool
    execution_authority: bool = False

def certify_events(category, events):
    ids=[e.canonical_event_id for e in events]
    return ExtractionCertification(
        category=category,
        events=len(events),
        unique_ids=len(set(ids)),
        stable_identity=(len(ids)==len(set(ids)) and all(x.startswith("osn:event:") for x in ids)),
        read_only=all(e.read_only is True for e in events),
    )
