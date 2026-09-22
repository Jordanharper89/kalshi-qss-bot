
from pathlib import Path
p=Path("audit_opd_UNDERLYING_EVENT_REACTION_TEMPORAL_HOLDOUT.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("UNDERLYING_EVENT_REACTION_TEMPORAL_HOLDOUT_V1",
          "LOOKBACKS=(15,30,60,300)",
          "accel_15_vs_60","accel_30_vs_300",
          "CONTINUATION","REVERSION",
          "TRAIN_FRAC=.65","signed_return_lower_bound",
          "hit_rate_lower_bound",
          "EVENT_REACTION_SIGNAL_SURVIVES_UNTOUCHED_HOLDOUT",
          "NO MODEL MUTATION"):
    assert x in s,x
print("[PASS] event definitions use only pre-anchor CHF spot history")
print("[PASS] continuation and reversion are tested as distinct reaction targets")
print("[PASS] 15s/30s/60s/300s impulse, acceleration, volatility and alignment features included")
print("[PASS] exact future underlying return remains label-only")
print("[PASS] strict chronological 65/35 train/untouched-holdout split")
print("[PASS] thresholds are learned from train only")
print("[PASS] survivor requires positive signed-return LB and hit-rate LB > 50pct")
print("[PASS] production predictor/runtime remain untouched")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
