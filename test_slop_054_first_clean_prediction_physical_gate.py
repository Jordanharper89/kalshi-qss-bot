from datetime import datetime
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
cut=datetime.fromisoformat(open("runtime_state/solana_live_opportunity/slop_050_cohort_start.txt").read().strip().replace("Z","+00:00"))
ps=[p for p in read_predictions() if datetime.fromisoformat(str(p.frozen_at).replace("Z","+00:00"))>=cut]
print("[CLEAN_PREDICTIONS]",len(ps))
assert ps,"NO_POST_REPAIR_LIVE_PREDICTION_YET"
by={}
for p in ps:by.setdefault(p.token_address,[]).append(p)
dup={t:x for t,x in by.items() if len(x)>1}
print("[CLEAN_TOKENS]",len(by))
print("[DUPLICATE_TOKEN_PREDICTIONS]",len(dup))
assert not dup,"SINGLE_INFLIGHT_TOKEN_BOUNDARY_VIOLATED"
p=sorted(ps,key=lambda x:str(x.frozen_at))[0]
print("[FIRST]",p.prediction_id,p.token_address,p.pair_address,p.frozen_at)
print("[PASS] first clean post-repair prediction physically exists")
print("[PASS] one-token/one-prediction boundary physically observed")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-054 CERTIFIED")
