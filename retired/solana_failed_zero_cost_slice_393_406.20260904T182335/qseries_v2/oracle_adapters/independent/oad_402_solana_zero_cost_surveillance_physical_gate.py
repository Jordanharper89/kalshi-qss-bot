from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import socket
import time
import urllib.error

from .oad_399_solana_zero_cost_continuous_surveillance_worker import (
    run_zero_cost_continuous_surveillance,
)
from .oad_400_solana_live_coverage_telemetry import capture_live_coverage

EXECUTION_AUTHORITY = False

_TRANSIENT_MARKERS = (
    "timed out",
    "timeout",
    "too many requests",
    "429",
    "rate limit",
    "temporarily unavailable",
    "connection reset",
    "connection aborted",
    "connection refused",
    "remote end closed",
    "network is unreachable",
    "name or service not known",
    "temporary failure",
)

@dataclass(frozen=True, slots=True)
class ZeroCostPhysicalCertification:
    before_lag: int
    after_lag: int
    before_checkpoint: int | None
    after_checkpoint: int | None
    attempts: int
    admitted_cycles: int
    transient_failures: int
    hard_failures: int
    checkpoint_advanced: bool
    lag_not_worse: bool
    state: str
    execution_authority: bool = False

def _is_transient_rpc_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    if "postgresql ingestion" in msg or "database" in msg or "psycopg" in msg:
        return False
    if isinstance(exc, (socket.timeout, urllib.error.URLError)):
        return True
    if isinstance(exc, TimeoutError):
        return True
    return any(marker in msg for marker in _TRANSIENT_MARKERS)

def _checkpoint_advanced(before, after) -> bool:
    b = before.last_committed_slot
    a = after.last_committed_slot
    if b is None:
        return isinstance(a, int)
    return isinstance(a, int) and a > b

def _lag_not_materially_worse(before_lag: int, after_lag: int, tolerance_slots: int = 16) -> bool:
    return int(after_lag) <= int(before_lag) + int(tolerance_slots)

def run_zero_cost_physical_gate(
    root=None,
    attempts: int = 5,
    backoff_seconds=(2.0, 4.0, 8.0, 10.0),
    progress=None,
    sleep_fn=time.sleep,
):
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    r = Path(root).resolve() if root else Path.cwd().resolve()
    before = capture_live_coverage(r)

    admitted_cycles = 0
    transient_failures = 0
    hard_failures = 0
    attempts_used = 0

    after = before

    for idx in range(attempts):
        attempts_used += 1

        try:
            run = run_zero_cost_continuous_surveillance(
                root=r,
                max_cycles=1,
                progress=progress,
                sleep_fn=sleep_fn,
            )
            admitted_cycles += int(getattr(run, "admitted_cycles", 0))

        except Exception as exc:
            if not _is_transient_rpc_error(exc):
                hard_failures += 1
                raise

            transient_failures += 1
            if progress:
                progress(
                    "[TRANSIENT-RPC]",
                    f"attempt={attempts_used}",
                    type(exc).__name__,
                    str(exc),
                )

        # Always re-read the durable state after the attempt, including failed attempts.
        # A worker may have committed before the public endpoint failed on a later request.
        try:
            after = capture_live_coverage(r)
        except Exception as exc:
            if not _is_transient_rpc_error(exc):
                hard_failures += 1
                raise

            transient_failures += 1
            if progress:
                progress(
                    "[TRANSIENT-HEAD]",
                    f"attempt={attempts_used}",
                    type(exc).__name__,
                    str(exc),
                )

        if _checkpoint_advanced(before, after):
            break

        if idx < attempts - 1:
            delay = float(backoff_seconds[min(idx, len(backoff_seconds) - 1)])
            if progress:
                progress("[BACKOFF]", f"seconds={delay}")
            sleep_fn(delay)

    advanced = _checkpoint_advanced(before, after)
    lag_ok = _lag_not_materially_worse(before.checkpoint_lag, after.checkpoint_lag)

    state = (
        "ZERO_COST_SURVEILLANCE_CERTIFIED"
        if advanced and lag_ok and hard_failures == 0
        else "ZERO_COST_SURVEILLANCE_NOT_CERTIFIED"
    )

    return ZeroCostPhysicalCertification(
        before_lag=int(before.checkpoint_lag),
        after_lag=int(after.checkpoint_lag),
        before_checkpoint=before.last_committed_slot,
        after_checkpoint=after.last_committed_slot,
        attempts=attempts_used,
        admitted_cycles=admitted_cycles,
        transient_failures=transient_failures,
        hard_failures=hard_failures,
        checkpoint_advanced=advanced,
        lag_not_worse=lag_ok,
        state=state,
        execution_authority=False,
    )
