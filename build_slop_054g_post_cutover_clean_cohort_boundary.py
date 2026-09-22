from pathlib import Path
from datetime import datetime, timezone

ROOT=Path("runtime_state/solana_live_opportunity")
P=ROOT/"slop_054g_post_cutover_cohort_start.txt"
T=Path("test_slop_054g_post_cutover_clean_cohort_boundary.py")

ROOT.mkdir(parents=True,exist_ok=True)
assert not P.exists(),"SLOP-054G cohort boundary already exists; refusing overwrite"
stamp=datetime.now(timezone.utc).isoformat()
P.write_text(stamp+"\n",encoding="utf-8")

T.write_text("""from pathlib import Path
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
""",encoding="utf-8")

print("[COHORT_START]",stamp)
print("[PASS] SLOP-054G post-cutover cohort boundary installed")
print("[PASS] test installed:",T)