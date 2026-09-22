from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json, os, time

from .oad_310_solana_target_token_wallet_trader_single_writer_persistence import (
    persist_target_token_wallet_trader_coverage,
)

READ_ONLY = True
PROBABILITY_ENABLED = False
DIRECTION_ENABLED = False
PUBLICATION_ALLOWED = False
EXECUTION_AUTHORITY = False

CHECKPOINT_RELATIVE = Path("runtime_state") / "oad_311_solana_wallet_trader_coverage_runtime.json"
DEFAULT_SUCCESS_INTERVAL_SECONDS = 300.0
DEFAULT_ERROR_BACKOFF_SECONDS = 300.0

@dataclass(frozen=True, slots=True)
class CoverageRuntimeCycle:
    cycle_sequence: int
    token_address: str | None
    state: str
    acquisition_state: str | None
    persistence_state: str | None
    committed_new: int
    exact_readback: int
    retry_after_seconds: float
    next_attempt_at: str
    observed_at: str
    failure_detail: str | None
    execution_authority: bool = False

def _utcnow():
    return datetime.now(timezone.utc)

def _checkpoint_path(root=None):
    return Path(root or Path.cwd()).resolve() / CHECKPOINT_RELATIVE

def _read_checkpoint(root=None):
    p = _checkpoint_path(root)
    if not p.is_file():
        return {}
    try:
        x = json.loads(p.read_text(encoding="utf-8"))
        return x if isinstance(x, dict) else {}
    except Exception:
        return {}

def _write_checkpoint(cycle, root=None):
    p = _checkpoint_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    q = p.with_suffix(p.suffix + ".tmp")
    q.write_text(json.dumps(asdict(cycle), sort_keys=True, indent=2) + "\n",
                 encoding="utf-8", newline="\n")
    os.replace(q, p)

def run_coverage_cycle(
    root=None,
    timeout_seconds=120.0,
    acquisition_timeout_seconds=30.0,
    success_interval_seconds=DEFAULT_SUCCESS_INTERVAL_SECONDS,
    error_backoff_seconds=DEFAULT_ERROR_BACKOFF_SECONDS,
):
    root = Path(root or Path.cwd()).resolve()
    prior = _read_checkpoint(root)
    seq = int(prior.get("cycle_sequence") or 0) + 1
    now = _utcnow()

    try:
        x = persist_target_token_wallet_trader_coverage(
            root=root,
            timeout_seconds=timeout_seconds,
            acquisition_timeout_seconds=acquisition_timeout_seconds,
        )
        if x.acquisition_state == "RATE_LIMITED_HOLD":
            retry = max(1.0, float(x.retry_after_seconds or DEFAULT_ERROR_BACKOFF_SECONDS))
            state = "RATE_LIMITED_HOLD"
        else:
            retry = max(1.0, float(success_interval_seconds))
            state = "SUCCESS"
        cycle = CoverageRuntimeCycle(
            seq, x.token_address, state, x.acquisition_state, x.persistence_state,
            int(x.committed_new), int(x.exact_readback), retry,
            (now + timedelta(seconds=retry)).isoformat(),
            now.isoformat(), None, False,
        )
    except Exception as e:
        retry = max(1.0, float(error_backoff_seconds))
        cycle = CoverageRuntimeCycle(
            seq, prior.get("token_address"), "ERROR_BACKOFF", None, None, 0, 0,
            retry, (now + timedelta(seconds=retry)).isoformat(),
            now.isoformat(), (type(e).__name__ + ": " + str(e))[:500], False,
        )

    _write_checkpoint(cycle, root)
    return cycle

def run_continuous_coverage(
    root=None,
    timeout_seconds=120.0,
    acquisition_timeout_seconds=30.0,
    success_interval_seconds=DEFAULT_SUCCESS_INTERVAL_SECONDS,
    error_backoff_seconds=DEFAULT_ERROR_BACKOFF_SECONDS,
):
    while True:
        cycle = run_coverage_cycle(
            root=root,
            timeout_seconds=timeout_seconds,
            acquisition_timeout_seconds=acquisition_timeout_seconds,
            success_interval_seconds=success_interval_seconds,
            error_backoff_seconds=error_backoff_seconds,
        )
        print(
            "[OAD-311] cycle=%s state=%s token=%s committed_new=%s exact_readback=%s "
            "retry_after_seconds=%s next_attempt_at=%s"
            % (
                cycle.cycle_sequence, cycle.state, cycle.token_address,
                cycle.committed_new, cycle.exact_readback,
                cycle.retry_after_seconds, cycle.next_attempt_at,
            ),
            flush=True,
        )
        time.sleep(cycle.retry_after_seconds)
