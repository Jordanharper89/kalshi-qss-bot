from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from .oad_128_official_bls_economic_adapter import acquire_bls_latest_economic_observations
from .oad_129_official_treasury_fiscal_data_adapter import acquire_treasury_debt_observation

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class EconomicProviderResult:
    provider: str
    state: str
    observations: tuple
    observation_count: int
    error_type: str|None
    error_message: str|None
    checked_at: str
    read_only: bool=True
    probability_enabled: bool=False
    execution_authority: bool=False

def _now():
    return datetime.now(timezone.utc).isoformat()

def _run_provider(provider: str, fn: Callable, timeout_seconds: float):
    try:
        rows=tuple(fn(timeout_seconds))
        return EconomicProviderResult(provider,"AVAILABLE",rows,len(rows),None,None,_now())
    except Exception as exc:
        return EconomicProviderResult(
            provider,"UNAVAILABLE",tuple(),0,type(exc).__name__,str(exc),_now()
        )

def acquire_resilient_authoritative_economic(timeout_seconds=20.0):
    results=(
        _run_provider("api.bls.gov",acquire_bls_latest_economic_observations,timeout_seconds),
        _run_provider("api.fiscaldata.treasury.gov",acquire_treasury_debt_observation,timeout_seconds),
    )
    observations=tuple(o for r in results if r.state=="AVAILABLE" for o in r.observations)
    return results,observations
