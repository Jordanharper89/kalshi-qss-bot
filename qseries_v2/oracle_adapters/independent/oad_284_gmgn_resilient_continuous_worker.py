from __future__ import annotations
from datetime import datetime, timezone
import time

from .oad_279_gmgn_solana_token_intelligence_adapter import GMGNRateLimitError
from .oad_281_gmgn_solana_single_writer_postgresql_persistence import persist_gmgn_solana_token_intelligence
from .oad_282_gmgn_continuous_production_policy import default_gmgn_continuous_policy, verify_gmgn_continuous_policy
from .oad_283_gmgn_continuous_runtime_checkpoint import (
    load_gmgn_runtime_checkpoint,
    save_gmgn_runtime_checkpoint,
    advance_success,
    advance_failure,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

def run_gmgn_cycle(root=None,policy=None):
    p=policy or default_gmgn_continuous_policy()
    if not verify_gmgn_continuous_policy(p):
        raise RuntimeError("invalid GMGN policy")
    cp=load_gmgn_runtime_checkpoint(root)
    try:
        result=persist_gmgn_solana_token_intelligence(
            root=root,
            timeout_seconds=p.persistence_timeout_seconds,
            acquisition_timeout_seconds=p.acquisition_timeout_seconds,
        )
        cp=advance_success(cp,result.token_address,result.observation_ids)
        save_gmgn_runtime_checkpoint(cp,root)
        return result,cp
    except Exception as exc:
        cp=advance_failure(cp,exc)
        save_gmgn_runtime_checkpoint(cp,root)
        raise

def _rate_limit_wait(exc):
    if not isinstance(exc,GMGNRateLimitError):
        return None

    wait=getattr(exc,"retry_after_seconds",None)
    try:
        wait=float(wait) if wait is not None else None
    except Exception:
        wait=None

    reset_at=getattr(exc,"reset_at",None)
    try:
        reset_at=float(reset_at) if reset_at is not None else None
    except Exception:
        reset_at=None

    if reset_at is not None:
        wait=max(1.0,reset_at-time.time())
    if wait is None:
        wait=300.0
    return min(600.0,max(5.0,wait+2.0))

def _safe_error_detail(exc):
    if isinstance(exc,GMGNRateLimitError):
        reset_at=getattr(exc,"reset_at",None)
        if reset_at is not None:
            try:
                stamp=datetime.fromtimestamp(float(reset_at),tz=timezone.utc).isoformat()
                return "GMGN_RATE_LIMITED reset_at_utc="+stamp
            except Exception:
                pass
        return "GMGN_RATE_LIMITED cooldown_required"

    detail=" ".join(str(exc).replace("\r"," ").replace("\n"," ").split())
    return detail[:500] if detail else type(exc).__name__

def run_resilient_gmgn_worker(root=None,policy=None,max_cycles=None,progress=print):
    p=policy or default_gmgn_continuous_policy()
    completed=0
    backoff=p.initial_backoff_seconds

    while max_cycles is None or completed<int(max_cycles):
        started=time.monotonic()
        try:
            result,cp=run_gmgn_cycle(root,p)
            completed+=1
            backoff=p.initial_backoff_seconds
            progress(
                f"[GMGN] cycle={cp.cycles} status=SUCCESS "
                f"token={result.token_address} committed_new={result.committed_new} "
                f"exact_readback={result.exact_readback} execution_authority=FALSE"
            )
            elapsed=time.monotonic()-started
            if max_cycles is None or completed<int(max_cycles):
                time.sleep(max(0.0,p.cadence_seconds-elapsed))

        except KeyboardInterrupt:
            raise

        except Exception as exc:
            completed+=1
            cp=load_gmgn_runtime_checkpoint(root)
            provider_wait=_rate_limit_wait(exc)

            if provider_wait is not None:
                retry_in=provider_wait
                reason=_safe_error_detail(exc)
                progress(
                    f"[GMGN] cycle={cp.cycles} status=COOLDOWN "
                    f"error={reason} retry_in={retry_in:.1f}s "
                    f"execution_authority=FALSE"
                )
                backoff=p.initial_backoff_seconds
            else:
                retry_in=backoff
                reason=_safe_error_detail(exc)
                progress(
                    f"[GMGN] cycle={cp.cycles} status=RETRY "
                    f"error_type={type(exc).__name__} detail={reason} "
                    f"retry_in={retry_in:.1f}s execution_authority=FALSE"
                )
                backoff=min(
                    p.max_backoff_seconds,
                    max(p.initial_backoff_seconds,backoff*2.0),
                )

            if max_cycles is None or completed<int(max_cycles):
                time.sleep(retry_in)

    return load_gmgn_runtime_checkpoint(root)
