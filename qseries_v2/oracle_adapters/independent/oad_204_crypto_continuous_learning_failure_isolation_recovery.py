from __future__ import annotations
from dataclasses import dataclass
import time
from .oad_202_crypto_continuous_learning_worker_policy import build_crypto_continuous_learning_worker_policy,failure_backoff_seconds
from .oad_203_crypto_continuous_learning_repeated_cycle_worker import run_crypto_continuous_learning_worker_cycle

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class ResilientCryptoLearningWorkerState:
    attempted_cycles:int
    successful_cycles:int
    failed_cycles:int
    consecutive_failures:int
    degraded:bool
    last_checkpoint:int
    last_error_type:str
    last_error_message:str
    execution_authority:bool=False

def run_resilient_crypto_learning_worker(
    root=None,policy=None,max_attempts=None,progress=print,sleep_fn=time.sleep
):
    p=policy or build_crypto_continuous_learning_worker_policy()
    attempted=successful=failed=consecutive=0
    last_checkpoint=0
    last_type=last_message=""
    while max_attempts is None or attempted<int(max_attempts):
        attempted+=1
        try:
            r=run_crypto_continuous_learning_worker_cycle(root,p,attempted)
            if not r.physical_ready:
                raise RuntimeError("continuous learning cycle returned physical_ready=False")
            successful+=1
            consecutive=0
            last_checkpoint=r.checkpoint_after
            if progress:
                progress(f"[CRYPTO-LEARN PASS] attempt={attempted} checkpoint={last_checkpoint}")
            if max_attempts is None or attempted<int(max_attempts):
                sleep_fn(p.cadence_seconds)
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            failed+=1
            consecutive+=1
            last_type=type(exc).__name__
            last_message=str(exc)
            delay=failure_backoff_seconds(p,consecutive)
            if progress:
                progress(
                    f"[CRYPTO-LEARN RECOVERY] attempt={attempted} failure={last_type} "
                    f"consecutive={consecutive} retry_in={delay:.3f}s"
                )
            if max_attempts is None or attempted<int(max_attempts):
                sleep_fn(delay)
    return ResilientCryptoLearningWorkerState(
        attempted,successful,failed,consecutive,
        consecutive>=p.max_consecutive_failures_before_degraded,
        last_checkpoint,last_type,last_message,False
    )
