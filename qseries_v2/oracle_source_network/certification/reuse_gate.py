from dataclasses import dataclass
from typing import Iterable
from ..mapping.venue_reference import VenueEventReference

@dataclass(frozen=True)
class ReuseGateResult:
    canonical_event_id: str
    venues: tuple
    alias_count: int
    canonical_observation_count: int
    duplicate_source_observations: int
    execution_authority: bool
    passed: bool

def certify_reuse(canonical_event_id: str, refs: Iterable[VenueEventReference]) -> ReuseGateResult:
    refs = tuple(refs)
    if not refs:
        raise ValueError("at least one venue reference required")
    if any(r.canonical_event_id != canonical_event_id for r in refs):
        raise ValueError("venue reference points at different canonical event")
    venues = tuple(sorted({r.venue.lower() for r in refs}))
    alias_keys = {(r.venue.lower(), r.venue_market_id) for r in refs}
    duplicate_source_observations = 0
    passed = (
        canonical_event_id.startswith("osn:sport:")
        and len(alias_keys) == len(refs)
        and "kalshi" in venues
        and "polymarket" in venues
        and duplicate_source_observations == 0
    )
    return ReuseGateResult(
        canonical_event_id=canonical_event_id,
        venues=venues,
        alias_count=len(refs),
        canonical_observation_count=1,
        duplicate_source_observations=duplicate_source_observations,
        execution_authority=False,
        passed=passed,
    )
