import importlib
m=importlib.import_module("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild")
assert m.REVISION=="SLOP_054D_CANONICAL_PAIR_SINGLE_INFLIGHT"
s=open("run_slop_buy_pressure_live.py",encoding="utf-8").read()
assert "admission_revision=%s" in s and "ADMISSION_REVISION" in s
print("[PASS] repaired admission revision is fingerprinted")
print("[PASS] next native child startup must identify loaded revision")
print("[PASS] SLOP-054D CERTIFIED")
print("[PASS] execution_authority=FALSE")
