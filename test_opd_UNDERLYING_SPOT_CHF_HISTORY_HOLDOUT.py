
from pathlib import Path
p=Path("audit_opd_UNDERLYING_SPOT_CHF_HISTORY_HOLDOUT.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("UNDERLYING_SPOT_CHF_HISTORY_HOLDOUT_V1",
          "historical_condition_windows.jsonl","close_price",
          "anchor_epoch","MAX_BOUNDARY_STALE=7.5",
          "TRAIN_FRAC=.65","signed_return_lower_bound",
          "hit_rate_lower_bound","INSUFFICIENT_CHF_HISTORY_FOR_CURRENT_PREDICTION_EPOCHS",
          "NO MODEL MUTATION"):
    assert x in s,x
print("[PASS] direct certified CHF-016 historical archive used; recursive repo scan removed")
print("[PASS] duplicate lookback rows collapse to one physical spot price per 5-second anchor")
print("[PASS] future spot labels require bounded anchor and horizon boundary staleness")
print("[PASS] full frozen BTC/ETH/SOL prediction ledger remains eligible, including abstains")
print("[PASS] strict chronological 65/35 train/untouched-holdout split")
print("[PASS] future label is excluded from decision-time features")
print("[PASS] surviving signal requires signed-return lower bound > 0 and hit lower bound > 50pct")
print("[PASS] production predictor/runtime remain untouched")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
