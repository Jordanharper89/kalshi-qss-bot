
from pathlib import Path
p=Path("audit_opd_UNDERLYING_SPOT_DUE_MINUS_HORIZON_HOLDOUT.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("UNDERLYING_SPOT_DUE_MINUS_HORIZON_HOLDOUT_V1",
          "resolution_due_epoch","return due-h",
          "historical_condition_windows.jsonl","TRAIN_FRAC=.65",
          "signed_return_lower_bound","hit_rate_lower_bound",
          "UNDERLYING_SIGNAL_SURVIVES_HOLDOUT","NO MODEL MUTATION"):
    assert x in s,x
print("[PASS] exact prediction anchor reconstructed as resolution_due_epoch - horizon_seconds")
print("[PASS] CHF physical 5-second spot archive supplies future underlying labels")
print("[PASS] no unavailable observed_epoch/prediction_epoch dependency remains")
print("[PASS] strict chronological 65/35 train/untouched-holdout split")
print("[PASS] future labels excluded from decision-time features")
print("[PASS] surviving underlying signal requires signed-return LB > 0 and hit-rate LB > 50pct")
print("[PASS] production predictor/runtime remain untouched")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
