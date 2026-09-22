from __future__ import annotations
from dataclasses import dataclass
import inspect, time
from pathlib import Path
from .oad_326_solana_universal_resilient_worker import run_solana_universal_worker_cycle
from .oad_393_solana_zero_cost_public_rpc_budget_governor import SolanaPublicRpcBudgetGovernor

EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class GovernedCycleResult:
    admitted:bool
    wait_seconds:float
    raw_type:str|None
    raw_result:object|None
    execution_authority:bool=False

def _invoke_existing_worker(root=None, progress=None):
    fn=run_solana_universal_worker_cycle
    sig=inspect.signature(fn)
    kwargs={}
    for p in sig.parameters.values():
        low=p.name.lower()
        if low in {"root","repo_root","repository_root"}:
            kwargs[p.name]=Path(root).resolve() if root else Path.cwd().resolve()
        elif low in {"progress","progress_fn","progress_callback"}:
            kwargs[p.name]=progress or (lambda *a,**k: None)
        elif p.default is not inspect._empty:
            continue
        else:
            raise RuntimeError("unsupported required OAD-326 parameter: "+p.name+" in "+str(sig))
    return fn(**kwargs)

def run_governed_solana_worker_cycle(root=None, governor=None, progress=None, sleep_fn=time.sleep):
    g=governor or SolanaPublicRpcBudgetGovernor()
    wait=g.wait_seconds("universal_worker_cycle")
    if wait>0:
        return GovernedCycleResult(False,float(wait),None,None,False)
    if not g.admit("universal_worker_cycle"):
        return GovernedCycleResult(False,float(g.wait_seconds("universal_worker_cycle")),None,None,False)
    try:
        raw=_invoke_existing_worker(root=root,progress=progress)
        return GovernedCycleResult(True,0.0,type(raw).__name__,raw,False)
    except Exception as e:
        msg=str(e).lower()
        if "429" in msg or "too many requests" in msg or "rate limit" in msg:
            g.record_throttle()
        raise