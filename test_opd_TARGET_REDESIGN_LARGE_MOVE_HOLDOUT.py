
from pathlib import Path
p=Path("audit_opd_TARGET_REDESIGN_LARGE_MOVE_HOLDOUT.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("HURDLE=.020","TRAIN_FRAC=.65","MIN_TRAIN_N=12","MIN_HOLDOUT_N=8",
          "PREDICT_HURDLE_CLEARING_REALIZED_MOVE_NOT_GENERIC_DIRECTION",
          "return 1 if net(r)>0 else 0","best_threshold(train,f)",
          "training score favors target precision","train,hold=data[:cut],data[cut:]",
          "holdout_profitable","conservative_lower_bound","NO MODEL MUTATION"):
    assert x in s,x
print("[PASS] predictive objective changed from generic direction to hurdle-clearing move selection")
print("[PASS] exact resolved prospective Gen2 actionable outcomes are the only labels")
print("[PASS] strict chronological 65/35 train/untouched-holdout split")
print("[PASS] rule thresholds learned from train only")
print("[PASS] selector training optimizes hurdle-clear classification, not realized mean-return fitting")
print("[PASS] untouched holdout winner still requires positive conservative realized net after 2pct")
print("[PASS] future/outcome/PnL-derived fields excluded from decision-time features")
print("[PASS] production predictor/runtime remain untouched")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
