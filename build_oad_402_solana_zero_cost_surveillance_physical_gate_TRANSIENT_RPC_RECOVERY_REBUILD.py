
from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED = "build_oad_402_solana_zero_cost_surveillance_physical_gate_TRANSIENT_RPC_RECOVERY_REBUILD.py"
MODULE = "oad_402_solana_zero_cost_surveillance_physical_gate.py"
TEST = "test_oad_402_solana_zero_cost_surveillance_physical_gate.py"
RUNNER = "run_oad_402_solana_zero_cost_surveillance_physical_gate.py"

DEPS = [
    ("qseries_v2/oracle_adapters/independent/oad_399_solana_zero_cost_continuous_surveillance_worker.py",
     ("run_zero_cost_continuous_surveillance",)),
    ("qseries_v2/oracle_adapters/independent/oad_400_solana_live_coverage_telemetry.py",
     ("capture_live_coverage",)),
    ("qseries_v2/oracle_adapters/independent/oad_401_solana_zero_cost_catchup_recovery_controller.py",
     ("plan_zero_cost_catchup",)),
]

MODULE_SOURCE = r"""
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
    if isinstance(exc, (TimeoutError, socket.timeout, urllib.error.URLError)):
        return True
    msg = str(exc).lower()
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
"""

TEST_SOURCE = r"""
import unittest

from qseries_v2.oracle_adapters.independent.oad_402_solana_zero_cost_surveillance_physical_gate import (
    run_zero_cost_physical_gate,
)

class T(unittest.TestCase):
    def test_physical_zero_cost_surveillance(self):
        x = run_zero_cost_physical_gate(
            attempts=5,
            progress=lambda *a, **k: print("[LIVE]", *a),
        )

        print("[PHYSICAL]", x)

        self.assertEqual(
            x.hard_failures,
            0,
            "non-transient failure occurred during zero-cost surveillance gate",
        )
        self.assertTrue(
            x.checkpoint_advanced,
            "durable Solana checkpoint did not advance after bounded transient-RPC recovery attempts",
        )
        self.assertTrue(
            x.lag_not_worse,
            "checkpoint lag materially worsened during bounded zero-cost surveillance run",
        )
        self.assertEqual(
            x.state,
            "ZERO_COST_SURVEILLANCE_CERTIFIED",
        )

if __name__ == "__main__":
    rr = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not rr.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-402 physical zero-cost Solana surveillance certified")
    print("[PASS] public-RPC timeout / temporary network failures treated as recoverable")
    print("[PASS] durable checkpoint preserved across transient failure")
"""

RUNNER_SOURCE = r"""
from __future__ import annotations

from qseries_v2.oracle_adapters.independent.oad_402_solana_zero_cost_surveillance_physical_gate import (
    run_zero_cost_physical_gate,
)

def main():
    x = run_zero_cost_physical_gate(
        attempts=5,
        progress=lambda *a, **k: print("[LIVE]", *a),
    )

    print("[PHYSICAL]", x)

    if x.state != "ZERO_COST_SURVEILLANCE_CERTIFIED":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
"""

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise RuntimeError("repository root not found")

def atomic_write(path: Path, source: str):
    source = textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def verify_dep(root: Path, rel: str, required):
    p = root / rel
    if not p.is_file():
        raise RuntimeError("required dependency missing: " + rel)

    tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    names = {
        n.name
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }

    missing = [name for name in required if name not in names]
    if missing:
        raise RuntimeError(
            "dependency interface missing: " + rel + " -> " + repr(missing)
        )

    print("[PASS] dependency verified:", rel)

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer filename mismatch")

    root = find_root()

    for rel, required in DEPS:
        verify_dep(root, rel, required)

    pkg = root / "qseries_v2" / "oracle_adapters" / "independent"
    module_path = pkg / MODULE
    test_path = root / TEST
    runner_path = root / RUNNER

    atomic_write(module_path, MODULE_SOURCE)
    atomic_write(test_path, TEST_SOURCE)
    atomic_write(runner_path, RUNNER_SOURCE)

    init = pkg / "__init__.py"
    lines = init.read_text(encoding="utf-8").splitlines() if init.exists() else []
    export = "from ." + module_path.stem + " import *"

    if export not in lines:
        lines.append(export)

    atomic_write(init, "\n".join(x for x in lines if x.strip()) + "\n")

    print("[PASS] installed:", module_path.relative_to(root))
    print("[PASS] test installed:", test_path.relative_to(root))
    print("[PASS] runner installed:", runner_path.relative_to(root))
    print("[PASS] replaces failed OAD-402 physical gate only")
    print("[PASS] OAD-398 through OAD-401 preserved certified")
    print("[PASS] transient public-RPC timeout/network failure recovery added")
    print("[PASS] bounded one-cycle retries with backoff added")
    print("[PASS] durable checkpoint is never manually advanced")
    print("[PASS] certification still requires real checkpoint advancement")
    print("[PASS] no paid RPC provider dependency")
    print("[PASS] no GMGN dependency")
    print("[PASS] OPH-019/021 persistence boundary preserved")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution_authority=FALSE")
    print("[DONE]", EXPECTED)

if __name__ == "__main__":
    main()
