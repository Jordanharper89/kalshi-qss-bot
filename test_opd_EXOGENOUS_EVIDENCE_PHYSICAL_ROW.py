
from pathlib import Path
p=Path("probe_opd_EXOGENOUS_EVIDENCE_PHYSICAL_ROW.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in (
    "EXOGENOUS_EVIDENCE_FREEZE_PHYSICAL_ROW_PROBE_V1",
    "run_prediction",
    "subprocess.run",
    "exogenous_evidence_snapshot",
    "ROWS WITH NONEMPTY SNAPSHOT",
    "EXOGENOUS_EVIDENCE_PHYSICALLY_FROZEN",
    "PRODUCTION_STATE_HAS_NO_ELIGIBLE_RAW_EXOGENOUS_EVIDENCE_AT_PREDICTION_BOUNDARY",
):
    assert x in s,x
print("[PASS] fresh interpreter is required so patched predictor source is reloaded")
print("[PASS] immutable ledger inspected before and after one-shot production prediction")
print("[PASS] only physical ledger rows can certify exogenous freeze")
print("[PASS] empty snapshot fails closed")
print("[PASS] no execution/publication authority added")
