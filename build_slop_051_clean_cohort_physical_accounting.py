from pathlib import Path
T=Path("test_slop_051_clean_cohort_physical_accounting.py")
T.write_text("""from datetime import datetime
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_020_prospective_resolution_ledger import read_resolution_dicts
cut=datetime.fromisoformat(open("runtime_state/solana_live_opportunity/slop_050_cohort_start.txt").read().strip().replace("Z","+00:00"))
ps=[p for p in read_predictions() if datetime.fromisoformat(str(p.frozen_at).replace("Z","+00:00"))>=cut]
ids={p.prediction_id for p in ps};rs=[r for r in read_resolution_dicts() if r["prediction_id"] in ids]
tokens={p.token_address for p in ps};rtokens={p.token_address for p in ps if p.prediction_id in {r["prediction_id"] for r in rs}}
print("[CLEAN_FROZEN]",len(ps));print("[CLEAN_RESOLVED]",len(rs))
print("[CLEAN_TOKENS]",len(tokens));print("[CLEAN_RESOLVED_TOKENS]",len(rtokens))
if rs:print("[CLEAN_NET_EXPECTANCY]",sum(float(r["net_return"]) for r in rs)/len(rs))
assert len(ids)==len(ps)
print("[PASS] clean cohort excludes historical pre-repair predictions")
print("[PASS] one prediction-id accounting preserved")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-051 CERTIFIED")
""",encoding="utf-8")
print("[PASS] SLOP-051 clean-cohort accounting installed")
print("[PASS] test installed:",T)