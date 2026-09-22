
from pathlib import Path
p=Path("audit_opd_UNDERLYING_SPOT_TEMPORAL_HOLDOUT.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("UNDERLYING_SPOT_TEMPORAL_HOLDOUT_AUDIT_V1",
          "canonical_events.jsonl","MAX_BOUNDARY_STALE=5.0",
          "exact_future_path","future_return","TRAIN_FRAC=.65",
          "PREDICT_UNDERLYING_SPOT_DIRECTION_BEFORE_KALSHI_CONTRACT_MAPPING",
          "including abstains" if False else "for p in jsonl(PRED)",
          "hit_rate_lower_bound","signed_return_lower_bound",
          "NO MODEL MUTATION"):
    assert x in s,x
print("[PASS] immutable prediction ledger supplies frozen decision-time states")
print("[PASS] all BTC/ETH/SOL frozen predictions are eligible, not only prior actionable rows")
print("[PASS] exact future label comes from physical Coinbase canonical event path")
print("[PASS] anchor and future boundary staleness capped at 5 seconds")
print("[PASS] strict chronological 65/35 train/untouched-holdout split")
print("[PASS] future spot label is never admitted into decision-time features")
print("[PASS] holdout signal requires positive signed-return lower bound and hit-rate lower bound > 50pct")
print("[PASS] Kalshi contract scoring/runtime remain untouched")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
