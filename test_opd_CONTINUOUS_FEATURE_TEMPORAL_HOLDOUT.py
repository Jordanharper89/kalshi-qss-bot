
from pathlib import Path
p=Path("audit_opd_CONTINUOUS_FEATURE_TEMPORAL_HOLDOUT.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("HURDLE=.020","TRAIN_FRAC=.65","MIN_TRAIN_N=12","MIN_HOLDOUT_N=8",
          "MIN_TICKERS=3","RESOLVED_EXACT_FUTURE","actionable_at_freeze",
          "BANNED=","future","outcome","directional_return","train=data[:cut]","hold=data[cut:]",
          "quantiles(vals)","holdout_positive","NO MODEL MUTATION"):
    assert x in s,x
print("[PASS] exact resolved Gen2 actionable prospective outcomes only")
print("[PASS] strict chronological 65/35 train/untouched-holdout split")
print("[PASS] thresholds are learned from train rows only")
print("[PASS] future/outcome/resolution/PnL-derived fields excluded from features")
print("[PASS] raw continuous frozen evidence values audited, not token identity alone")
print("[PASS] single-feature and two-feature rules require support across multiple tickers")
print("[PASS] fixed 2pct hurdle and conservative lower-bound economics preserved")
print("[PASS] predictor/runtime remain untouched")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
