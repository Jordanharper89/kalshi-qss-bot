from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone

from .oad_118_persisted_authoritative_sports_cohort import load_persisted_authoritative_sports_cohort
from .oad_119_persisted_sports_structured_descriptor import descriptors_from_persisted_sports_rows
from .oad_120_current_market_sports_team_pair_index import fetch_current_market_sports_candidates

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True, slots=True)
class LiveSportsEndToEndEvidenceReport:
    persisted_observations: int
    committed_new: int
    providers: tuple
    structured_descriptors: int
    current_markets: int
    observations_with_candidates: int
    association_candidates: int
    descriptors: tuple
    associations: tuple
    certified_at: str
    read_only: bool=True
    probability_enabled: bool=False
    execution_authority: bool=False

def run_live_sports_end_to_end_evidence_certification(
    root=None,
    market_limit=1000,
    timeout_seconds=120.0,
    acquisition_timeout_seconds=20.0,
    market_timeout_seconds=20.0,
):
    cohort=load_persisted_authoritative_sports_cohort(
        root=root,
        timeout_seconds=timeout_seconds,
        acquisition_timeout_seconds=acquisition_timeout_seconds,
    )
    descriptors=descriptors_from_persisted_sports_rows(cohort.rows)
    markets,groups=fetch_current_market_sports_candidates(
        descriptors,
        limit=market_limit,
        timeout_seconds=market_timeout_seconds,
    )
    flat=tuple(x for _,xs in groups for x in xs)
    with_candidates=sum(1 for _,xs in groups if xs)
    if any(getattr(x,"candidate_only",None) is not True for x in flat):
        raise RuntimeError("sports association escaped candidate-only boundary")
    return LiveSportsEndToEndEvidenceReport(
        persisted_observations=int(cohort.cohort_size),
        committed_new=int(cohort.committed_new),
        providers=tuple(cohort.providers),
        structured_descriptors=len(descriptors),
        current_markets=len(markets),
        observations_with_candidates=with_candidates,
        association_candidates=len(flat),
        descriptors=tuple(descriptors),
        associations=flat,
        certified_at=datetime.now(timezone.utc).isoformat(),
        read_only=True,
        probability_enabled=False,
        execution_authority=False,
    )
