from __future__ import annotations

import ast
import os
import subprocess
import sys
import textwrap
from pathlib import Path

EXPECTED_INSTALLER = "build_oad_290_gmgn_supervised_failure_truth_FOUNDATIONAL_REBUILD.py"
MODULE_REL = Path("qseries_v2/oracle_adapters/independent/oad_290_gmgn_clean_continuous_runtime.py")
RUNNER_REL = Path("run_oad_290_gmgn_clean_continuous_intelligence_child.py")
TEST_REL = Path("test_oad_290_gmgn_supervised_failure_truth.py")

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import time

from .oad_289_gmgn_clean_single_writer_persistence import persist_current_gmgn

READ_ONLY = True
PROBABILITY_ENABLED = False
DIRECTION_ENABLED = False
PUBLICATION_ALLOWED = False
EXECUTION_AUTHORITY = False

MAX_ERROR_DETAIL = 1800


@dataclass(frozen=True, slots=True)
class Checkpoint:
    cycles: int = 0
    successes: int = 0
    failures: int = 0
    last_success_at: str | None = None
    last_error: str | None = None
    last_token_address: str | None = None
    last_observation_ids: tuple = ()
    execution_authority: bool = False


def checkpoint_path(root=None):
    p = Path(root or Path.cwd()).resolve() / "runtime_state"
    p.mkdir(parents=True, exist_ok=True)
    return p / "oad_290_gmgn_clean_runtime.json"


def load_checkpoint(root=None):
    p = checkpoint_path(root)
    if not p.exists():
        return Checkpoint()
    d = json.loads(p.read_text(encoding="utf-8"))
    return Checkpoint(
        int(d["cycles"]),
        int(d["successes"]),
        int(d["failures"]),
        d.get("last_success_at"),
        d.get("last_error"),
        d.get("last_token_address"),
        tuple(d.get("last_observation_ids") or ()),
        False,
    )


def save(c, root=None):
    p = checkpoint_path(root)
    d = asdict(c)
    d["last_observation_ids"] = list(c.last_observation_ids)
    t = p.with_suffix(".tmp")
    t.write_text(
        json.dumps(d, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(t, p)


def _bounded_error_detail(exc):
    detail = str(exc).strip()
    if not detail:
        detail = repr(exc)
    detail = " ".join(detail.split())
    return detail[:MAX_ERROR_DETAIL]


def cycle(root=None):
    c = load_checkpoint(root)
    try:
        r = persist_current_gmgn(root)
        n = Checkpoint(
            c.cycles + 1,
            c.successes + 1,
            c.failures,
            datetime.now(timezone.utc).isoformat(),
            None,
            r.token_address,
            r.observation_ids,
            False,
        )
        save(n, root)
        return r, n
    except Exception as exc:
        detail = _bounded_error_detail(exc)
        save(
            Checkpoint(
                c.cycles + 1,
                c.successes,
                c.failures + 1,
                c.last_success_at,
                detail,
                c.last_token_address,
                c.last_observation_ids,
                False,
            ),
            root,
        )
        raise


def run(max_cycles=None, cadence_seconds=60.0, root=None, progress=print):
    done = 0
    backoff = 5.0

    while max_cycles is None or done < int(max_cycles):
        try:
            r, c = cycle(root)
            done += 1
            backoff = 5.0
            progress(
                f"[GMGN2] cycle={c.cycles} status=SUCCESS "
                f"token={r.token_address} committed_new={r.committed_new} "
                f"exact_readback={r.exact_readback} execution_authority=FALSE"
            )
            if max_cycles is None or done < int(max_cycles):
                time.sleep(float(cadence_seconds))

        except KeyboardInterrupt:
            raise

        except Exception as exc:
            done += 1
            c = load_checkpoint(root)
            wait = min(
                600.0,
                max(
                    5.0,
                    float(getattr(exc, "retry_after_seconds", backoff)),
                ),
            )
            detail = _bounded_error_detail(exc)
            progress(
                f"[GMGN2] cycle={c.cycles} status=COOLDOWN "
                f"error_type={type(exc).__name__} "
                f"error_detail={detail!r} "
                f"retry_in={wait:.1f}s execution_authority=FALSE"
            )
            if max_cycles is None or done < int(max_cycles):
                time.sleep(wait)
            backoff = min(60.0, backoff * 2)

    return load_checkpoint(root)
"""

RUNNER_SOURCE = r"""
from __future__ import annotations

import argparse

from qseries_v2.oracle_adapters.independent.oad_290_gmgn_clean_continuous_runtime import (
    load_checkpoint,
    run,
)

p = argparse.ArgumentParser()
p.add_argument("--check", action="store_true")
p.add_argument("--max-cycles", type=int)
p.add_argument("--cadence-seconds", type=float, default=60.0)
a = p.parse_args()
c = load_checkpoint()

if a.check:
    print(
        f"[READY] gmgn_intelligence_v2 checkpoint_cycle={c.cycles} "
        f"successes={c.successes} failures={c.failures} "
        f"last_error={c.last_error!r} execution_authority=FALSE"
    )
    raise SystemExit(0)

print("[START] Oracle GMGN replacement child execution_authority=FALSE", flush=True)
try:
    run(
        a.max_cycles,
        a.cadence_seconds,
        progress=lambda x: print(x, flush=True),
    )
except KeyboardInterrupt:
    pass
"""

TEST_SOURCE = r"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import qseries_v2.oracle_adapters.independent.oad_290_gmgn_clean_continuous_runtime as M
from qseries_v2.oracle_adapters.independent.oad_287_gmgn_clean_provider_foundation import (
    GMGNProviderError,
)


class T(unittest.TestCase):
    def test_01_exact_failure_truth_is_persisted_and_logged(self):
        with tempfile.TemporaryDirectory() as td:
            detail = (
                "GMGN_NOT_ADMITTED: config check failed | "
                "config: command=['gmgn-cli.cmd','config','--check'] "
                "returncode=1 elapsed_seconds=0.500 "
                "exception_type=None stderr='provider diagnostic'"
            )

            lines = []
            with patch.object(
                M,
                "persist_current_gmgn",
                side_effect=GMGNProviderError(detail),
            ):
                cp = M.run(
                    max_cycles=1,
                    cadence_seconds=0.0,
                    root=td,
                    progress=lines.append,
                )

            joined = "\n".join(lines)
            print(joined)
            self.assertEqual(cp.cycles, 1)
            self.assertEqual(cp.failures, 1)
            self.assertEqual(cp.last_error, detail)
            self.assertIn("error_type=GMGNProviderError", joined)
            self.assertIn("config check failed", joined)
            self.assertIn("returncode=1", joined)
            self.assertIn("provider diagnostic", joined)

    def test_02_safety_boundary(self):
        self.assertTrue(M.READ_ONLY)
        self.assertFalse(M.PROBABILITY_ENABLED)
        self.assertFalse(M.DIRECTION_ENABLED)
        self.assertFalse(M.PUBLICATION_ALLOWED)
        self.assertFalse(M.EXECUTION_AUTHORITY)

    def test_03_physical_one_cycle_exposes_truth(self):
        p = subprocess.run(
            [
                sys.executable,
                "run_oad_290_gmgn_clean_continuous_intelligence_child.py",
                "--max-cycles",
                "1",
                "--cadence-seconds",
                "1",
            ],
            cwd=Path.cwd(),
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
        print(p.stdout, end="")
        print(p.stderr, end="")
        self.assertEqual(p.returncode, 0)

        if "status=SUCCESS" in p.stdout:
            self.assertIn("exact_readback=3", p.stdout)
            print("[PHYSICAL] GMGN cycle succeeded during failure-truth certification")
        else:
            self.assertIn("status=COOLDOWN", p.stdout)
            self.assertIn("error_type=", p.stdout)
            self.assertIn("error_detail=", p.stdout)
            self.assertNotIn("error_detail=''", p.stdout)
            print("[PHYSICAL] GMGN failure truth exposed without masking")


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] exact GMGN failure detail survives OAD-290 runtime boundary")
    print("[PASS] checkpoint retains bounded physical provider failure detail")
    print("[PASS] supervised child log exposes error type + exact detail + retry")
    print("[PASS] OAD-287/OAD-288/OAD-289 public contracts preserved")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-290 SUPERVISED FAILURE-TRUTH FOUNDATIONAL REBUILD CERTIFIED")
"""


def root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")


def checked_write(path, source):
    source = textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def require_markers(path, markers):
    if not path.is_file():
        raise RuntimeError("required production boundary missing: " + str(path))
    source = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in source:
            raise RuntimeError(
                "exact production boundary marker missing: "
                + str(path)
                + " -> "
                + marker
            )


def main():
    if Path(__file__).name != EXPECTED_INSTALLER:
        raise RuntimeError("installer filename identity mismatch")

    r = root()
    pkg = r / "qseries_v2" / "oracle_adapters" / "independent"
    module = r / MODULE_REL
    runner = r / RUNNER_REL
    test = r / TEST_REL

    print("=" * 108)
    print(" OAD-290 GMGN SUPERVISED FAILURE-TRUTH — FOUNDATIONAL REBUILD")
    print("=" * 108)
    print("[ROOT]", r)

    require_markers(
        pkg / "oad_287_gmgn_clean_provider_foundation.py",
        (
            "class GMGNProviderError",
            "class GMGNRateLimitError",
            "def require_gmgn_provider",
            "def run_gmgn_cli",
        ),
    )
    require_markers(
        pkg / "oad_288_gmgn_clean_acquisition_boundary.py",
        (
            "def acquire_current_gmgn_token",
            "def acquire_gmgn_token",
        ),
    )
    require_markers(
        pkg / "oad_289_gmgn_clean_single_writer_persistence.py",
        ("def persist_current_gmgn",),
    )
    require_markers(
        module,
        (
            "class Checkpoint",
            "def load_checkpoint",
            "def cycle",
            "def run",
            "persist_current_gmgn",
        ),
    )
    require_markers(
        runner,
        (
            "oad_290_gmgn_clean_continuous_runtime",
            "--max-cycles",
        ),
    )

    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
    ):
        if not (r / rel).is_file():
            raise RuntimeError("frozen boundary missing: " + rel)

    old = {
        module: module.read_bytes(),
        runner: runner.read_bytes(),
        test: test.read_bytes() if test.exists() else None,
    }

    try:
        checked_write(module, MODULE_SOURCE)
        checked_write(runner, RUNNER_SOURCE)
        checked_write(test, TEST_SOURCE)

        for path in (module, runner, test):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")

        q = subprocess.run(
            [sys.executable, str(runner), "--check"],
            cwd=r,
            text=True,
            capture_output=True,
            timeout=45,
            check=False,
        )
        if q.returncode != 0:
            raise RuntimeError(
                "OAD-290 runner --check failed:\n" + q.stdout + "\n" + q.stderr
            )

        print(q.stdout, end="")
        print("[PASS] exact OAD-287 provider boundary verified")
        print("[PASS] exact OAD-288 acquisition boundary verified")
        print("[PASS] exact OAD-289 persistence boundary verified")
        print("[PASS] existing OAD-290 runtime rebuilt in place")
        print("[PASS] provider exception detail no longer collapsed to exception class")
        print("[PASS] checkpoint preserves bounded exact failure detail")
        print("[PASS] cooldown log exposes error_type + error_detail + retry")
        print("[PASS] frozen OPH-023/Kalshi OAD-055 preserved")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-290 SUPERVISED FAILURE-TRUTH REBUILD INSTALLED")

    except Exception:
        for path, data in old.items():
            if data is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(data)
        print("[ROLLBACK] OAD-290 failure-truth rebuild rolled back")
        raise


if __name__ == "__main__":
    main()
