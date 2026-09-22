from __future__ import annotations
from dataclasses import dataclass
import time
from .oad_398_solana_zero_cost_governed_worker_cycle import run_governed_solana_worker_cycle
from .oad_393_solana_zero_cost_public_rpc_budget_governor import SolanaPublicRpcBudgetGovernor,SolanaRpcBudgetPolicy

EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class ContinuousSurveillanceRun:
    requested_cycles:int
    admitted_cycles:int
    throttled_cycles:int
    failures:int
    raw_types:tuple
    execution_authority:bool=False

def run_zero_cost_continuous_surveillance(root=None,max_cycles=3,progress=None,sleep_fn=time.sleep,governor=None):
    if max_cycles<1: raise ValueError("max_cycles must be >= 1")
    g=governor or SolanaPublicRpcBudgetGovernor(SolanaRpcBudgetPolicy(
        window_seconds=10,total_requests_per_window=20,per_method_requests_per_window=8,min_spacing_seconds=0.5,max_backoff_seconds=30
    ))
    admitted=throttled=failures=0
    raw=[]
    for cycle in range(1,max_cycles+1):
        try:
            r=run_governed_solana_worker_cycle(root=root,governor=g,progress=progress,sleep_fn=sleep_fn)
            if r.admitted:
                admitted+=1
                raw.append(r.raw_type)
            else:
                throttled+=1
                if r.wait_seconds>0:
                    sleep_fn(r.wait_seconds)
        except Exception:
            failures+=1
            raise
    return ContinuousSurveillanceRun(max_cycles,admitted,throttled,failures,tuple(raw),False)