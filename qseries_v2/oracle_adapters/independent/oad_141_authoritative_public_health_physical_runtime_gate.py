from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from .oad_140_resilient_public_health_canonical_persistence import persist_resilient_public_health

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class PublicHealthPhysicalRuntimeGate:
    state:str
    provider_states:tuple
    available_providers:tuple
    unavailable_providers:tuple
    raw_observations:int
    canonical_observations:int
    committed_new:int
    exact_readback:int
    runtime_ready:bool
    certified_at:str
    read_only:bool=True
    probability_enabled:bool=False
    execution_authority:bool=False

def run_authoritative_public_health_physical_runtime_gate(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):
    p=persist_resilient_public_health(root,timeout_seconds,acquisition_timeout_seconds)
    available=tuple(sorted(x.provider for x in p.provider_results if x.state=="AVAILABLE"))
    unavailable=tuple(sorted(x.provider for x in p.provider_results if x.state!="AVAILABLE"))
    usable=len(available)>0 and p.raw_observations>0 and p.exact_readback==p.canonical_observations
    if not usable: raise RuntimeError("no usable authoritative public-health provider coverage")
    state="FULL_COVERAGE" if not unavailable else "PARTIAL_COVERAGE"
    return PublicHealthPhysicalRuntimeGate(
        state,tuple((x.provider,x.state,x.observation_count,x.error_type) for x in p.provider_results),
        available,unavailable,p.raw_observations,p.canonical_observations,p.committed_new,p.exact_readback,
        True,datetime.now(timezone.utc).isoformat(),True,False,False
    )
