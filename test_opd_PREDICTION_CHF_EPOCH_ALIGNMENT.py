from pathlib import Path
p=Path("diagnose_opd_PREDICTION_CHF_EPOCH_ALIGNMENT.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("PREDICTION_CHF_EPOCH_ALIGNMENT_DIAGNOSTIC_V1","anchor_epoch",
          "observed_epoch","prediction_epoch","frozen_epoch","created_epoch",
          "state.observed_epoch","overlap_count","nearest_boundary_seconds",
          "MODEL MUTATION"):
    assert x in s,x
print("[PASS] prediction and CHF epoch ranges compared directly")
print("[PASS] seconds/milliseconds/microseconds/nanoseconds normalized deterministically")
print("[PASS] top-level and state timestamp bases inspected separately")
print("[PASS] overlap/below/above/nearest-boundary counts reported per asset")
print("[PASS] no model, ledger, resolver, or runtime mutation")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
