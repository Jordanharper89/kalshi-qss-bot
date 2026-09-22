from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
from .oad_175_crypto_durable_temporal_intelligence_runtime import run_crypto_durable_temporal_intelligence
READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class CryptoDurableTemporalPhysicalCertification:
    seed_runtime_ready:bool; comparison_runtime_ready:bool; historical_states:int
    exact_prior_states:int; comparable_temporal_metrics:int; increased:int; decreased:int
    unchanged:int; no_comparable_history:int; cross_source_assets:tuple; exact_readback:int
    physical_ready:bool; certified_at:str; probability_enabled:bool=False
    direction_enabled:bool=False; execution_authority:bool=False

def run_crypto_durable_temporal_intelligence_physical_certification(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0,per_source_history_limit=512):
    seed_at=datetime.now(timezone.utc)
    seed=run_crypto_durable_temporal_intelligence(root,timeout_seconds,acquisition_timeout_seconds,per_source_history_limit,seed_at)
    comp_at=max(datetime.now(timezone.utc),seed_at+timedelta(microseconds=1))
    comp=run_crypto_durable_temporal_intelligence(root,timeout_seconds,acquisition_timeout_seconds,per_source_history_limit,comp_at)
    ready=bool(seed.runtime_ready and comp.runtime_ready and comp.historical_states>0 and comp.exact_prior_states>0 and comp.comparable_temporal_metrics>0 and comp.exact_readback==comp.current_states and comp.cross_source_assets)
    if not ready:
        raise RuntimeError(f"durable crypto temporal certification failed; seed_ready={seed.runtime_ready}; comp_ready={comp.runtime_ready}; history={comp.historical_states}; prior={comp.exact_prior_states}; comparable={comp.comparable_temporal_metrics}; readback={comp.exact_readback}")
    return CryptoDurableTemporalPhysicalCertification(seed.runtime_ready,comp.runtime_ready,comp.historical_states,comp.exact_prior_states,comp.comparable_temporal_metrics,comp.increased,comp.decreased,comp.unchanged,comp.no_comparable_history,comp.cross_source_assets,comp.exact_readback,True,datetime.now(timezone.utc).isoformat(),False,False,False)
