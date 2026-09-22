from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone

from .oad_134_resilient_authoritative_economic_canonical_persistence import persist_resilient_authoritative_economic
from .oad_135_authoritative_economic_partial_coverage_certification import certify_economic_partial_coverage

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class ResilientEconomicPhysicalRuntimeGate:
    state: str
    provider_states: tuple
    available_providers: tuple
    unavailable_providers: tuple
    raw_observations: int
    canonical_observations: int
    committed_new: int
    exact_readback: int
    coverage_usable: bool
    runtime_ready: bool
    certified_at: str
    read_only: bool=True
    probability_enabled: bool=False
    execution_authority: bool=False

def run_resilient_authoritative_economic_physical_runtime_gate(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):
    p=persist_resilient_authoritative_economic(root,timeout_seconds,acquisition_timeout_seconds)
    c=certify_economic_partial_coverage(p)
    provider_states=tuple((x.provider,x.state,x.observation_count,x.error_type) for x in p.provider_results)
    runtime_ready=bool(c.coverage_usable)
    if not runtime_ready:
        raise RuntimeError("no usable authoritative economic provider coverage")
    return ResilientEconomicPhysicalRuntimeGate(
        c.state,provider_states,c.available_providers,c.unavailable_providers,
        p.raw_observations,p.canonical_observations,p.committed_new,p.exact_readback,
        c.coverage_usable,True,datetime.now(timezone.utc).isoformat(),True,False,False
    )
