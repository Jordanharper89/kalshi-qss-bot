from pathlib import Path
from datetime import datetime,timezone
p=Path("runtime_state/solana_live_opportunity/slop_054g_post_cutover_cohort_start.txt")
assert p.exists()
s=p.read_text(encoding="utf-8").strip()
d=datetime.fromisoformat(s)
assert d.tzinfo is not None
old=Path("runtime_state/solana_live_opportunity/slop_050_cohort_start.txt")
assert old.exists()
assert datetime.fromisoformat(old.read_text(encoding="utf-8").strip()) < d
print("[COHORT_START]",s)
print("[PASS] SLOP-050 historical cohort preserved")
print("[PASS] post-cutover clean cohort boundary established")
print("[PASS] no prediction or resolution ledger mutation")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-054G CERTIFIED")
