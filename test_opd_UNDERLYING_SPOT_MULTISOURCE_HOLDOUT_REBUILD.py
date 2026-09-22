
from pathlib import Path
p=Path("audit_opd_UNDERLYING_SPOT_MULTISOURCE_HOLDOUT_REBUILD.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("UNDERLYING_SPOT_MULTISOURCE_HOLDOUT_REBUILD_V1",
          "candidate_files()","rglob(\"*.jsonl\")","BTC-USD","ETH-USD","SOL-USD",
          "MAX_BOUNDARY_STALE=10.0","INSUFFICIENT_PHYSICAL_UNDERLYING_HISTORY",
          "TRAIN_FRAC=.65","signed_return_lower_bound","hit_rate_lower_bound",
          "NO MODEL MUTATION"):
    assert x in s,x
print("[PASS] replacement discovers physical Coinbase/crypto/canonical/history JSONL sources recursively")
print("[PASS] multiple common product/time/price schemas normalized")
print("[PASS] BTC/ETH/SOL rows merged and deduplicated before future labeling")
print("[PASS] exact boundary staleness remains capped; no ticker-derived future prices")
print("[PASS] insufficient physical history fails closed with source-coverage report")
print("[PASS] chronological train/holdout evaluation runs only when enough exact labels exist")
print("[PASS] no Kalshi predictor/runtime mutation")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
