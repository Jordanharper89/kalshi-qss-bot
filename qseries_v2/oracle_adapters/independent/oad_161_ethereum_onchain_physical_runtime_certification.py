from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from .oad_157_ethereum_onchain_evidence_foundation import ALLOWED_PROVIDER_MAP
from .oad_160_ethereum_onchain_canonical_postgresql_persistence import persist_current_ethereum_onchain

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class EthereumPhysicalRuntimeCertification:
    state:str
    raw_observations:int
    canonical_observations:int
    committed_new:int
    exact_readback:int
    providers:tuple
    source_class:str
    independent_evidence:bool
    runtime_ready:bool
    certified_at:str
    read_only:bool=True
    probability_enabled:bool=False
    execution_authority:bool=False

def run_ethereum_onchain_physical_runtime_certification(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):
    p=persist_current_ethereum_onchain(root,timeout_seconds,acquisition_timeout_seconds)
    providers=set(p.providers)
    ready=(
        p.raw_observations>=4
        and p.canonical_observations==p.raw_observations
        and p.exact_readback==p.canonical_observations
        and bool(providers)
        and providers.issubset(set(ALLOWED_PROVIDER_MAP))
    )
    if not ready:
        raise RuntimeError("Ethereum on-chain physical runtime certification failed")
    return EthereumPhysicalRuntimeCertification(
        "READY",p.raw_observations,p.canonical_observations,p.committed_new,p.exact_readback,p.providers,
        "underlying_chain_state_observation",True,True,datetime.now(timezone.utc).isoformat(),True,False,False)
