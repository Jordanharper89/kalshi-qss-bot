from __future__ import annotations
from dataclasses import dataclass
import time
from pathlib import Path

from .oad_272_solana_continuous_observation_policy import build_solana_continuous_observation_policy,verify_solana_continuous_observation_policy
from .oad_273_solana_pinned_pool_live_snapshot_persistence import select_live_solana_token,persist_pinned_solana_pool_snapshot
from .oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history,build_multi_horizon_solana_states

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaContinuousCycle:
    cycle:int
    token_address:str
    acquired:bool
    observation_id:str|None
    history_records:int
    windows:tuple
    state:str
    execution_authority:bool=False

@dataclass(frozen=True,slots=True)
class SolanaContinuousWorkerState:
    attempts:int
    successful_cycles:int
    failed_cycles:int
    consecutive_failures:int
    token_address:str|None
    last_state:str
    execution_authority:bool=False

def failure_backoff_seconds(policy,consecutive_failures):
    n=max(1,int(consecutive_failures))
    return min(policy.failure_backoff_max_seconds,policy.failure_backoff_base_seconds*(2**(n-1)))

def run_solana_continuous_cycle(root=None,policy=None,cycle=1,token_address=None):
    root=Path(root or Path.cwd()).resolve()
    p=policy or build_solana_continuous_observation_policy()
    if not verify_solana_continuous_observation_policy(p):
        raise RuntimeError("invalid OAD-272 policy")
    token=str(token_address or select_live_solana_token(p.acquisition_timeout_seconds))
    snap=persist_pinned_solana_pool_snapshot(
        token,root=root,
        timeout_seconds=p.persistence_timeout_seconds,
        acquisition_timeout_seconds=p.acquisition_timeout_seconds,
    )
    history=read_pinned_pool_history(token,root=root,limit=p.history_limit)
    windows=build_multi_horizon_solana_states(history,token,p.windows_seconds)
    state="OBSERVING" if history else "HOLD_NO_HISTORY"
    return SolanaContinuousCycle(int(cycle),token,True,snap.observation_id,len(history),windows,state,False)

def run_resilient_solana_continuous_worker(
    root=None,policy=None,max_cycles=None,progress=print,sleep_fn=time.sleep
):
    root=Path(root or Path.cwd()).resolve()
    p=policy or build_solana_continuous_observation_policy()
    token=None; attempts=0; ok=0; failed=0; consecutive=0; last="STARTING"
    cycle=0
    while max_cycles is None or attempts<int(max_cycles):
        attempts+=1; cycle+=1
        try:
            if token is None:
                token=select_live_solana_token(p.acquisition_timeout_seconds)
                progress("[PIN] token_address="+token)
            r=run_solana_continuous_cycle(root,p,cycle,token)
            ok+=1; consecutive=0; last=r.state
            ready=tuple((w.window_seconds,w.records,w.state) for w in r.windows)
            progress(f"[CYCLE] cycle={cycle} token={token} history={r.history_records} windows={ready} execution_authority=FALSE")
            if max_cycles is None or attempts<int(max_cycles):
                sleep_fn(p.acquisition_seconds)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            failed+=1; consecutive+=1; last="DEGRADED"
            progress(f"[ERROR] cycle={cycle} type={type(e).__name__} message={e}")
            if max_cycles is None or attempts<int(max_cycles):
                sleep_fn(failure_backoff_seconds(p,consecutive))
    return SolanaContinuousWorkerState(attempts,ok,failed,consecutive,token,last,False)
