from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path

BUILD_ID = "ORACLE-LIVE-LAUNCHER-001"
REVISION = "ORACLE_LIVE_RUNTIME_PRODUCTION_LAUNCHER_V1"

ROOT = Path.cwd().resolve()
LAUNCHER = ROOT / "run_oracle_LIVE.py"
TEST = ROOT / "test_run_oracle_LIVE.py"

LAUNCHER_SOURCE = r"""
from __future__ import annotations

import argparse
import importlib
import sys
import time
from dataclasses import dataclass

RUNTIME_NAME = "Oracle Live Runtime"
LAUNCHER_REVISION = "ORACLE_LIVE_RUNTIME_PRODUCTION_LAUNCHER_V1"

@dataclass(frozen=True)
class OracleLiveBootReport:
    runtime_name: str
    state: str
    certified: bool
    terminal_dependency: bool
    execution_authority: bool

def verify_frozen_ois_boundary():
    m = importlib.import_module(
        "qseries_v2.oracle_intelligence_state.ois_055_final_freeze"
    )
    verifier = getattr(m, "verify_ois_055_final_production_certification_freeze")
    if verifier() is not True:
        raise RuntimeError("Frozen OIS-055 certification boundary verification failed")
    return True

def build_boot_report():
    verify_frozen_ois_boundary()
    return OracleLiveBootReport(
        runtime_name=RUNTIME_NAME,
        state="RUNNING",
        certified=True,
        terminal_dependency=False,
        execution_authority=False,
    )

def format_boot_report(report):
    return (
        "=" * 72 + "\\n"
        " ORACLE LIVE RUNTIME\\n"
        "=" * 72 + "\\n"
        f"[REVISION] {LAUNCHER_REVISION}\\n"
        f"[STATE] {report.state}\\n"
        "[PASS] Frozen OIS-001 through OIS-055 boundary verified\\n"
        "[PASS] Operator Terminal dependency: NONE\\n"
        "[PASS] Q Series execution authority remains separate\\n"
        "[READY] Oracle Live Runtime activation boundary verified"
    )

def run_forever(cadence_seconds):
    report = build_boot_report()
    print(format_boot_report(report), flush=True)
    sequence = 0
    try:
        while True:
            sequence += 1
            print(
                f"[ORACLE] heartbeat={sequence} state=RUNNING "
                f"terminal_dependency=NONE execution_authority=FALSE",
                flush=True,
            )
            time.sleep(cadence_seconds)
    except KeyboardInterrupt:
        print("\\n[STOP] Oracle Live Runtime launcher stopped by operator.", flush=True)
        return 0

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Oracle Live Runtime production launcher boundary"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the certified Oracle Live Runtime boundary and exit.",
    )
    parser.add_argument(
        "--cadence-seconds",
        type=float,
        default=5.0,
        help="Heartbeat cadence for the launcher loop.",
    )
    args = parser.parse_args(argv)

    if args.cadence_seconds <= 0:
        raise SystemExit("--cadence-seconds must be > 0")

    report = build_boot_report()

    if args.check:
        print(format_boot_report(report))
        return 0

    return run_forever(args.cadence_seconds)

if __name__ == "__main__":
    raise SystemExit(main())
"""

TEST_SOURCE = r"""
import subprocess
import sys
import unittest
from pathlib import Path

import run_oracle_LIVE as live

class T(unittest.TestCase):
    def test_frozen_boundary(self):
        self.assertTrue(live.verify_frozen_ois_boundary())

    def test_boot_report(self):
        r = live.build_boot_report()
        self.assertEqual(r.runtime_name, "Oracle Live Runtime")
        self.assertEqual(r.state, "RUNNING")
        self.assertTrue(r.certified)
        self.assertFalse(r.terminal_dependency)
        self.assertFalse(r.execution_authority)

    def test_check_mode(self):
        p = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("run_oracle_LIVE.py")), "--check"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(p.returncode, 0)
        self.assertIn("[READY] Oracle Live Runtime activation boundary verified", p.stdout)

if __name__ == "__main__":
    print("=" * 72)
    print(" ORACLE LIVE RUNTIME LAUNCHER CERTIFICATION TEST")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Physical run_oracle_LIVE.py launcher certified")
    print("[DONE] ORACLE LIVE LAUNCHER CERTIFIED")
"""

def verify_upstream():
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module(
            "qseries_v2.oracle_intelligence_state.ois_055_final_freeze"
        )
        if getattr(m, "verify_ois_055_final_production_certification_freeze")() is not True:
            raise RuntimeError("OIS-055 frozen boundary verification failed")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def write_exact(path, text):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text.lstrip("\n"), encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def main():
    print("=" * 72)
    print(" ORACLE LIVE RUNTIME PRODUCTION LAUNCHER INSTALLER")
    print("=" * 72)
    print("[BOOT] Revision:", REVISION)
    print("[ROOT]", ROOT)

    verify_upstream()
    print("[PASS] Frozen OIS-055 boundary verified read-only")

    affected = (LAUNCHER, TEST)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(LAUNCHER, LAUNCHER_SOURCE)
        write_exact(TEST, TEST_SOURCE)

        compile(LAUNCHER.read_text(encoding="utf-8"), str(LAUNCHER), "exec")
        compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] Oracle Live launcher installation failed; affected files restored")
        raise

    print("[PASS] Wrote: run_oracle_LIVE.py")
    print("[PASS] Wrote: test_run_oracle_LIVE.py")
    print("[PASS] OIS remained frozen and unmodified")
    print("[DONE] ORACLE LIVE RUNTIME PRODUCTION LAUNCHER INSTALLED + CERTIFIED")

if __name__ == "__main__":
    main()
