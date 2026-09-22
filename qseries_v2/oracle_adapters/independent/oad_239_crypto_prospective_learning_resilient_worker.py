from __future__ import annotations
from dataclasses import dataclass
import time
from .oad_202_crypto_continuous_learning_worker_policy import build_crypto_continuous_learning_worker_policy,failure_backoff_seconds
from .oad_237_crypto_prospective_learning_cycle_activation import run_prospective_learning_cycle
from .oad_238_crypto_prospective_learning_state_refresh import refresh_prospective_learning_states
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class ProspectiveLearningWorkerState:
    attempted_cycles:int; successful_cycles:int; failed_cycles:int; consecutive_failures:int
    degraded:bool; last_checkpoint:int; last_scored_cases:int; last_admission_state:str
    last_error_type:str; last_error_message:str; execution_authority:bool=False

def run_resilient_prospective_learning_worker(root=None,policy=None,max_attempts=None,progress=print,sleep_fn=time.sleep):
    p=policy or build_crypto_continuous_learning_worker_policy()
    attempted=successful=failed=consecutive=0
    last_checkpoint=last_scored=0; last_admission="HOLD"; last_type=last_message=""
    while max_attempts is None or attempted<int(max_attempts):
        attempted+=1
        try:
            cycle=run_prospective_learning_cycle(root,p,attempted)
            if not cycle.physical_ready:
                raise RuntimeError("prospective learning cycle returned physical_ready=False")
            refresh=refresh_prospective_learning_states(root)
            successful+=1; consecutive=0
            last_checkpoint=int(cycle.checkpoint_after); last_scored=int(cycle.scored_cases)
            last_admission=str(refresh.admission_state)
            if progress:
                progress(f"[CRYPTO-PROSPECTIVE PASS] attempt={attempted} checkpoint={last_checkpoint} forecasts={cycle.forecasts} committed={cycle.forecasts_committed} scored={last_scored} admission={last_admission}")
            if max_attempts is None or attempted<int(max_attempts):
                sleep_fn(p.cadence_seconds)
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            failed+=1; consecutive+=1
            last_type=type(exc).__name__; last_message=str(exc)
            delay=failure_backoff_seconds(p,consecutive)
            if progress:
                progress(f"[CRYPTO-PROSPECTIVE RECOVERY] attempt={attempted} failure={last_type} consecutive={consecutive} retry_in={delay:.3f}s")
            if max_attempts is None or attempted<int(max_attempts):
                sleep_fn(delay)
    return ProspectiveLearningWorkerState(
        attempted,successful,failed,consecutive,
        consecutive>=p.max_consecutive_failures_before_degraded,
        last_checkpoint,last_scored,last_admission,last_type,last_message,False
    )
