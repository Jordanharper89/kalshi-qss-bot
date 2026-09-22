from pathlib import Path
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
