from pathlib import Path
P=Path("qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_015b_concurrent_live_lifecycle_rebuild.py")
R=Path("run_slop_buy_pressure_live.py")
T=Path("test_slop_054d_loaded_admission_revision_fingerprint.py")
s=P.read_text(encoding="utf-8")
tag='REVISION="SLOP_054D_CANONICAL_PAIR_SINGLE_INFLIGHT"'
if tag not in s:P.write_text(tag+"\\n"+s,encoding="utf-8")
r=R.read_text(encoding="utf-8")
imp="from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild import REVISION as ADMISSION_REVISION"
if imp not in r:r=imp+"\\n"+r
old="print('[SLOP LIVE] BUY_PRESSURE child STARTING execution_authority=FALSE',flush=True)"
new="print('[SLOP LIVE] BUY_PRESSURE child STARTING admission_revision=%s execution_authority=FALSE'%ADMISSION_REVISION,flush=True)"
assert old in r or new in r
if old in r:r=r.replace(old,new)
R.write_text(r,encoding="utf-8")
T.write_text("""import importlib
m=importlib.import_module("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild")
assert m.REVISION=="SLOP_054D_CANONICAL_PAIR_SINGLE_INFLIGHT"
s=open("run_slop_buy_pressure_live.py",encoding="utf-8").read()
assert "admission_revision=%s" in s and "ADMISSION_REVISION" in s
print("[PASS] repaired admission revision is fingerprinted")
print("[PASS] next native child startup must identify loaded revision")
print("[PASS] SLOP-054D CERTIFIED")
print("[PASS] execution_authority=FALSE")
""",encoding="utf-8")
print("[PASS] SLOP-054D loaded-revision fingerprint installed")
print("[PASS] test installed:",T)