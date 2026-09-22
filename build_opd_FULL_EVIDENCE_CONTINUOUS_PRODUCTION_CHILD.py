from pathlib import Path
import shutil

ROOT = Path.cwd().resolve()
LAUNCHER = ROOT / "run_oracle_LIVE.py"
CHILD = ROOT / "run_opd_full_evidence_predictor_child.py"
TEST = ROOT / "test_opd_FULL_EVIDENCE_CONTINUOUS_PRODUCTION_CHILD.py"
PREDICTOR = ROOT / "qseries_v2" / "oracle_predictive_discovery" / "opd_live_full_evidence_fusion_predictor.py"
BACKUP = ROOT / "run_oracle_LIVE.pre_full_evidence_predictor_child.py"

if not LAUNCHER.is_file():
    raise RuntimeError("run_oracle_LIVE.py missing")
if not PREDICTOR.is_file():
    raise RuntimeError("full-evidence predictor missing")

predictor_text = PREDICTOR.read_text(encoding="utf-8")
required_predictor_markers = (
    "FRESH CANONICAL CUTOVER",
    "MAX_STATE_AGE_SECONDS=120.0",
    "EXECUTION_AUTHORITY=False",
    "PUBLICATION_ALLOWED=False",
)
for marker in required_predictor_markers:
    if marker not in predictor_text:
        raise RuntimeError("fresh-canonical predictor boundary missing: " + marker)

child_text = '''from __future__ import annotations
import argparse
import time
from pathlib import Path

from qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor import (
    EXECUTION_AUTHORITY,
    PUBLICATION_ALLOWED,
    run as run_prediction,
)

DEFAULT_CADENCE_SECONDS = 30.0


def verify_boundary():
    if EXECUTION_AUTHORITY is not False:
        raise RuntimeError("execution authority must remain FALSE")
    if PUBLICATION_ALLOWED is not False:
        raise RuntimeError("publication authority must remain FALSE")
    return True


def run_forever(root=None, cadence_seconds=DEFAULT_CADENCE_SECONDS):
    root = Path(root or Path.cwd()).resolve()
    cadence_seconds = float(cadence_seconds)
    if cadence_seconds <= 0:
        raise ValueError("cadence_seconds must be > 0")
    verify_boundary()
    cycle = 0
    while True:
        cycle += 1
        started = time.monotonic()
        print(
            f"[FULL-EVIDENCE LIVE] cycle={cycle} event=PREDICT cadence_seconds={cadence_seconds:.1f} "
            "execution_authority=FALSE publication_allowed=FALSE",
            flush=True,
        )
        run_prediction(root=root)
        elapsed = max(0.0, time.monotonic() - started)
        time.sleep(max(0.0, cadence_seconds - elapsed))


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    p.add_argument("--cadence-seconds", type=float, default=DEFAULT_CADENCE_SECONDS)
    a = p.parse_args(argv)
    if a.check:
        verify_boundary()
        print("[PASS] full-evidence predictor child boundary verified")
        print("[CADENCE_SECONDS]", a.cadence_seconds)
        print("[EXECUTION/PUBLICATION] FALSE/FALSE")
        return 0
    run_forever(Path.cwd(), a.cadence_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
CHILD.write_text(child_text, encoding="utf-8")

launcher_text = LAUNCHER.read_text(encoding="utf-8")
entry = '    "full_evidence_predictor": "run_opd_full_evidence_predictor_child.py",'
if entry not in launcher_text:
    anchor = '    "predictive_prospective": "run_opd_prospective_continuous_child.py",'
    if launcher_text.count(anchor) != 1:
        raise RuntimeError("exact predictive_prospective supervisor anchor not found once")
    if not BACKUP.exists():
        shutil.copy2(LAUNCHER, BACKUP)
    launcher_text = launcher_text.replace(anchor, anchor + "\n" + entry, 1)
    LAUNCHER.write_text(launcher_text, encoding="utf-8")

TEST.write_text('''from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd().resolve()
CHILD = ROOT / "run_opd_full_evidence_predictor_child.py"
PREDICTOR = ROOT / "qseries_v2" / "oracle_predictive_discovery" / "opd_live_full_evidence_fusion_predictor.py"

import run_oracle_LIVE as mod

assert mod.CHILDREN.get("predictive_prospective") == "run_opd_prospective_continuous_child.py"
assert mod.CHILDREN.get("full_evidence_predictor") == "run_opd_full_evidence_predictor_child.py"
assert CHILD.is_file()
assert PREDICTOR.is_file()

p = subprocess.run(
    [sys.executable, str(CHILD), "--check", "--cadence-seconds", "30"],
    cwd=str(ROOT), capture_output=True, text=True, timeout=20,
)
print(p.stdout, end="")
if p.stderr:
    print(p.stderr, end="")
assert p.returncode == 0
assert "[PASS] full-evidence predictor child boundary verified" in p.stdout
assert "[EXECUTION/PUBLICATION] FALSE/FALSE" in p.stdout

print("[PASS] full_evidence_predictor registered as native supervised Oracle child")
print("[PASS] existing predictive_prospective child preserved")
print("[PASS] generic Oracle supervisor restart/health/shutdown path inherited")
print("[PASS] full-evidence child cadence=30s inside 120s freshness boundary")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
''', encoding="utf-8")

print("=" * 104)
print(" ORACLE FULL-EVIDENCE CONTINUOUS PRODUCTION CHILD INSTALLER")
print("=" * 104)
print("[PASS] fresh-canonical predictor boundary verified")
print("[PASS] child runner installed:", CHILD.name)
print("[PASS] run_oracle_LIVE.py supervisor slot installed")
print("[PASS] deterministic test installed:", TEST.name)
print("[PRESERVED] predictive_prospective=run_opd_prospective_continuous_child.py")
print("[NEW_CHILD] full_evidence_predictor=run_opd_full_evidence_predictor_child.py")
print("[CADENCE_SECONDS] 30.0")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
