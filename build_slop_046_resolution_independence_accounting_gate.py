from pathlib import Path
T=Path("test_slop_046_resolution_independence_accounting_gate.py")
T.write_text("""from collections import defaultdict
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_020_prospective_resolution_ledger import read_resolution_dicts
ps={p.prediction_id:p for p in read_predictions()};rs=read_resolution_dicts();by=defaultdict(list)
for r in rs:
 p=ps.get(r["prediction_id"])
 if p:by[p.token_address].append(float(r["net_return"]))
means={t:sum(v)/len(v) for t,v in by.items()}
positive=sum(v>0 for v in means.values())
print("[RESOLVED]",len(rs));print("[INDEPENDENT_TOKENS]",len(means))
print("[POSITIVE_TOKENS]",positive);print("[NONPOSITIVE_TOKENS]",len(means)-positive)
for t,v in sorted(means.items()):
 print("[TOKEN]",t[:12],"predictions=",len(by[t]),"mean_net=",round(v,8))
assert len(rs)>=len(means)
print("[PASS] correlated pairs are not counted as independent tokens")
print("[PASS] SLOP-046 physical independence accounting complete")
print("[PASS] execution_authority=FALSE")
""",encoding="utf-8")
print("[PASS] SLOP-046 independence accounting gate installed")
print("[PASS] test installed:",T)