from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class EconomicCoverageCertification:
    state: str
    available_providers: tuple
    unavailable_providers: tuple
    raw_observations: int
    exact_readback: int
    coverage_usable: bool
    full_provider_coverage: bool
    certified_at: str
    probability_enabled: bool=False
    execution_authority: bool=False

def certify_economic_partial_coverage(persistence_result):
    available=tuple(sorted(x.provider for x in persistence_result.provider_results if x.state=="AVAILABLE"))
    unavailable=tuple(sorted(x.provider for x in persistence_result.provider_results if x.state!="AVAILABLE"))
    usable=(
        len(available)>0
        and persistence_result.raw_observations>0
        and persistence_result.exact_readback==persistence_result.canonical_observations
    )
    full=usable and len(unavailable)==0
    if full:
        state="FULL_COVERAGE"
    elif usable:
        state="PARTIAL_COVERAGE"
    else:
        state="NO_USABLE_COVERAGE"
    return EconomicCoverageCertification(
        state,available,unavailable,int(persistence_result.raw_observations),
        int(persistence_result.exact_readback),usable,full,
        datetime.now(timezone.utc).isoformat(),False,False
    )
