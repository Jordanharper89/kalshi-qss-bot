from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from .oad_130_authoritative_economic_canonical_persistence import persist_current_authoritative_economic

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True,slots=True)
class AuthoritativeEconomicPhysicalGate:
    raw_observations:int
    canonical_observations:int
    provenance_validated:int
    already_present:int
    committed_new:int
    exact_readback:int
    providers:tuple
    certified:bool
    certified_at:str
    read_only:bool=True
    probability_enabled:bool=False
    execution_authority:bool=False

def run_authoritative_economic_physical_production_gate(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):
    r=persist_current_authoritative_economic(root,timeout_seconds,acquisition_timeout_seconds)
    certified=(
        r.raw_observations>0 and r.canonical_observations==r.raw_observations
        and r.provenance_validated==r.canonical_observations
        and r.exact_readback==r.canonical_observations
        and r.already_present+r.committed_new==r.canonical_observations
        and len(r.providers)>0
    )
    if not certified: raise RuntimeError("authoritative economic physical production certification failed")
    return AuthoritativeEconomicPhysicalGate(
        r.raw_observations,r.canonical_observations,r.provenance_validated,r.already_present,
        r.committed_new,r.exact_readback,r.providers,True,datetime.now(timezone.utc).isoformat(),
        True,False,False)
