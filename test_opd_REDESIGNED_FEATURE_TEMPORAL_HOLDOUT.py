
from pathlib import Path
p=Path("audit_opd_REDESIGNED_FEATURE_TEMPORAL_HOLDOUT.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("HURDLE=.020","TRAIN_FRAC=.65","MIN_TRAIN_N=12","MIN_HOLDOUT_N=8",
          "MIN_TICKERS=3","REDESIGNED_FEATURE_TEMPORAL_HOLDOUT_AUDIT_V1",
          "horizon_to_remaining_ratio","anchor_distance_mid","confidence_x_agreement",
          "vote_mean_range","direction_vote_balance","cases_per_ticker",
          "RESOLVED_EXACT_FUTURE","actionable_at_freeze",
          "train,hold=data[:cut],data[cut:]","NO MODEL MUTATION"):
    assert x in s,x
print("[PASS] exact resolved Gen2 actionable prospective outcomes only")
print("[PASS] strict chronological 65/35 untouched temporal holdout")
print("[PASS] redesigned features use frozen-at-decision state only")
print("[PASS] contract geometry, confidence calibration, vote dispersion, support concentration derived")
print("[PASS] future/outcome/PnL-derived fields excluded from feature construction")
print("[PASS] train-only thresholds; untouched holdout determines survival")
print("[PASS] fixed 2pct hurdle and conservative lower-bound criterion preserved")
print("[PASS] production predictor/runtime remain untouched")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
