from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_016b_exact_frozen_prediction_maturity_rebuild import materialize_frozen_prediction_path
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_017b_ordered_physical_economic_resolution import resolve_economics
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_020_prospective_resolution_ledger import persist_resolutions,read_resolution_dicts
R=Path.cwd();before={x["prediction_id"] for x in read_resolution_dicts(R)}
ready=[];economics=[]
for p in read_predictions(R):
 if p.prediction_id in before:continue
 path=materialize_frozen_prediction_path(p,root=R)
 if path is None:continue
 ready.append(p.prediction_id);e=resolve_economics(p,path)
 if e is not None:economics.append(e)
print("[MATURITY_READY]",len(ready));print("[ECONOMICS_READY]",len(economics))
assert economics,"no physically resolvable economics"
w=persist_resolutions(tuple(economics),R)
after={x["prediction_id"]:x for x in read_resolution_dicts(R)}
missing=[e.prediction_id for e in economics if e.prediction_id not in after]
print("[PERSIST]",w);print("[READBACK_MATCHED]",len(economics)-len(missing));print("[READBACK_MISSING]",len(missing))
assert not missing
for e in economics[:10]:print("[RESOLUTION]",e.prediction_id[:12],e.outcome,"net=",round(e.net_return,8))
print("[PASS] SLOP-045 physical maturity -> economics -> persistence -> readback")
print("[PASS] execution_authority=FALSE")
