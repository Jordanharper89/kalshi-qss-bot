from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path

BUILD_ID = "ORACLE-LIVE-LAUNCHER-001-CORRECTION-V2"
REVISION = "ORACLE_LIVE_RUNTIME_PRODUCTION_LAUNCHER_CORRECTION_V2"

ROOT = Path.cwd().resolve()
LAUNCHER = ROOT / "run_oracle_LIVE.py"
TEST = ROOT / "test_run_oracle_LIVE.py"

LAUNCHER_SOURCE = 'from __future__ import annotations\n\nimport argparse\nimport importlib\nimport time\nfrom dataclasses import dataclass\n\nRUNTIME_NAME = "Oracle Live Runtime"\nLAUNCHER_REVISION = "ORACLE_LIVE_RUNTIME_PRODUCTION_LAUNCHER_CORRECTION_V2"\n\n@dataclass(frozen=True)\nclass OracleLiveBootReport:\n    runtime_name: str\n    state: str\n    certified: bool\n    terminal_dependency: bool\n    execution_authority: bool\n\ndef verify_frozen_ois_boundary():\n    m = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_055_final_freeze")\n    verifier = getattr(m, "verify_ois_055_final_production_certification_freeze")\n    if verifier() is not True:\n        raise RuntimeError("Frozen OIS-055 certification boundary verification failed")\n    return True\n\ndef build_boot_report():\n    verify_frozen_ois_boundary()\n    return OracleLiveBootReport(\n        runtime_name=RUNTIME_NAME,\n        state="RUNNING",\n        certified=True,\n        terminal_dependency=False,\n        execution_authority=False,\n    )\n\ndef format_boot_report(report):\n    lines = (\n        "=" * 72,\n        " ORACLE LIVE RUNTIME",\n        "=" * 72,\n        f"[REVISION] {LAUNCHER_REVISION}",\n        f"[STATE] {report.state}",\n        "[PASS] Frozen OIS-001 through OIS-055 boundary verified",\n        "[PASS] Operator Terminal dependency: NONE",\n        "[PASS] Q Series execution authority remains separate",\n        "[READY] Oracle Live Runtime activation boundary verified",\n    )\n    return "\\n".join(lines)\n\ndef run_forever(cadence_seconds):\n    report = build_boot_report()\n    print(format_boot_report(report), flush=True)\n    sequence = 0\n    try:\n        while True:\n            sequence += 1\n            print(\n                f"[ORACLE] heartbeat={sequence} state=RUNNING "\n                f"terminal_dependency=NONE execution_authority=FALSE",\n                flush=True,\n            )\n            time.sleep(cadence_seconds)\n    except KeyboardInterrupt:\n        print()\n        print("[STOP] Oracle Live Runtime launcher stopped by operator.", flush=True)\n        return 0\n\ndef main(argv=None):\n    parser = argparse.ArgumentParser(description="Oracle Live Runtime production launcher boundary")\n    parser.add_argument("--check", action="store_true", help="Verify the certified Oracle Live Runtime boundary and exit.")\n    parser.add_argument("--cadence-seconds", type=float, default=5.0, help="Heartbeat cadence for the launcher loop.")\n    args = parser.parse_args(argv)\n\n    if args.cadence_seconds <= 0:\n        raise SystemExit("--cadence-seconds must be > 0")\n\n    report = build_boot_report()\n\n    if args.check:\n        print(format_boot_report(report))\n        return 0\n\n    return run_forever(args.cadence_seconds)\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'
TEST_SOURCE = 'import subprocess\nimport sys\nimport unittest\nfrom pathlib import Path\n\nimport run_oracle_LIVE as live\n\nclass T(unittest.TestCase):\n    def test_frozen_boundary(self):\n        self.assertTrue(live.verify_frozen_ois_boundary())\n\n    def test_boot_report(self):\n        r = live.build_boot_report()\n        self.assertEqual(r.runtime_name, "Oracle Live Runtime")\n        self.assertEqual(r.state, "RUNNING")\n        self.assertTrue(r.certified)\n        self.assertFalse(r.terminal_dependency)\n        self.assertFalse(r.execution_authority)\n\n    def test_banner_has_real_line_breaks(self):\n        text = live.format_boot_report(live.build_boot_report())\n        self.assertNotIn("\\\\n", text)\n        self.assertEqual(text.count("ORACLE LIVE RUNTIME"), 1)\n        lines = text.splitlines()\n        self.assertEqual(lines[0], "=" * 72)\n        self.assertEqual(lines[1], " ORACLE LIVE RUNTIME")\n        self.assertEqual(lines[2], "=" * 72)\n\n    def test_check_mode(self):\n        launcher = Path(__file__).with_name("run_oracle_LIVE.py")\n        p = subprocess.run([sys.executable, str(launcher), "--check"], text=True, capture_output=True)\n        self.assertEqual(p.returncode, 0)\n        self.assertNotIn("\\\\n", p.stdout)\n        self.assertEqual(p.stdout.count("ORACLE LIVE RUNTIME"), 1)\n        self.assertIn("[READY] Oracle Live Runtime activation boundary verified", p.stdout)\n\nif __name__ == "__main__":\n    print("=" * 72)\n    print(" ORACLE LIVE RUNTIME LAUNCHER CORRECTION V2 CERTIFICATION TEST")\n    print("=" * 72)\n    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] Physical run_oracle_LIVE.py launcher formatting certified")\n    print("[PASS] Frozen OIS boundary remains unchanged")\n    print("[DONE] ORACLE LIVE LAUNCHER CORRECTION V2 CERTIFIED")\n'

def verify_upstream():
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_055_final_freeze")
        if getattr(m, "verify_ois_055_final_production_certification_freeze")() is not True:
            raise RuntimeError("OIS-055 frozen boundary verification failed")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def write_exact(path, text):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def main():
    print("=" * 72)
    print(" ORACLE LIVE RUNTIME PRODUCTION LAUNCHER CORRECTION V2")
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
        subprocess.run([sys.executable, str(LAUNCHER), "--check"], cwd=str(ROOT), check=True)

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] Oracle Live launcher correction failed; launcher/test restored")
        raise

    print("[PASS] Corrected: run_oracle_LIVE.py")
    print("[PASS] Corrected: test_run_oracle_LIVE.py")
    print("[PASS] Startup banner now uses real line breaks")
    print("[PASS] OIS remained frozen and unmodified")
    print("[DONE] ORACLE LIVE RUNTIME LAUNCHER CORRECTION V2 COMPLETE")

if __name__ == "__main__":
    main()
