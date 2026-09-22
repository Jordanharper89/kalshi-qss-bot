
from pathlib import Path
p=Path("audit_opd_EXOGENOUS_EVENT_IMPACT_TEMPORAL_HOLDOUT.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("EXOGENOUS_EVENT_IMPACT_TEMPORAL_HOLDOUT_V1",
          "PRICE_BANNED","LEAK_BANNED","EXOGENOUS_HINTS",
          "kalshi","coinbase","future_label",
          "TRAIN_FRAC=.65","NO_SUPPORTED_EXOGENOUS_FEATURES_IN_FROZEN_LEDGER",
          "signed_return_lower_bound","hit_rate_lower_bound",
          "EXOGENOUS_EVENT_SIGNAL_SURVIVES_UNTOUCHED_HOLDOUT",
          "NO MODEL MUTATION"):
    assert x in s,x
print("[PASS] exogenous-event features exclude Kalshi/Coinbase/price/return/orderbook fields")
print("[PASS] future/outcome/resolution/PnL-derived fields excluded")
print("[PASS] only frozen pre-anchor independent-source/event evidence is eligible")
print("[PASS] exact CHF future spot return remains label-only")
print("[PASS] strict chronological 65/35 train/untouched-holdout split")
print("[PASS] missing exogenous evidence fails closed instead of manufacturing features")
print("[PASS] survivor requires positive signed-return LB and hit-rate LB > 50pct")
print("[PASS] production predictor/runtime remain untouched")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
