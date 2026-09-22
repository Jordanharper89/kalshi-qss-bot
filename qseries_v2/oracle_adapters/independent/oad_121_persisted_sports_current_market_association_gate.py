from __future__ import annotations
from dataclasses import dataclass

from .oad_118_persisted_authoritative_sports_cohort import load_persisted_authoritative_sports_cohort
from .oad_119_persisted_sports_structured_descriptor import descriptors_from_persisted_sports_rows
from .oad_120_current_market_sports_team_pair_index import fetch_current_market_sports_candidates

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True, slots=True)
class PersistedSportsAssociationReport:
    persisted_observations: int
    structured_descriptors: int
    current_markets: int
    observations_with_candidates: int
    association_candidates: int
    associations: tuple
    ready_for_reasoning_evidence_comparison: bool
    execution_authority: bool=False

def run_persisted_sports_current_market_association_gate(
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
    return PersistedSportsAssociationReport(
        persisted_observations=cohort.cohort_size,
        structured_descriptors=len(descriptors),
        current_markets=len(markets),
        observations_with_candidates=with_candidates,
        association_candidates=len(flat),
        associations=flat,
        ready_for_reasoning_evidence_comparison=bool(flat),
        execution_authority=False,
    )
