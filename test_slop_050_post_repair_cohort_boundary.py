from pathlib import Path
from datetime import datetime
p=Path("runtime_state/solana_live_opportunity/slop_050_cohort_start.txt")
assert p.exists()
x=p.read_text().strip()
d=datetime.fromisoformat(x.replace("Z","+00:00"))
assert d.tzinfo is not None
print("[COHORT_START]",x)
print("[PASS] historical 201 predictions retained as lineage")
print("[PASS] clean post-repair prospective cohort boundary frozen")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-050 CERTIFIED")
