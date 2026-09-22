
from qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence import select_live_solana_token
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import build_outcome_pending_solana_cases
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002_physical_exact_future_price_path_materialization import materialize_exact_future_price_paths
def certify_existing_history(root=None,limit=512):
 token=select_live_solana_token(20.0)
 rows=tuple(read_pinned_pool_history(token,root=root,limit=limit))
 if len(rows)<2: raise AssertionError("insufficient existing persisted history")
 cases=tuple(build_outcome_pending_solana_cases(rows,horizons=(5,15,30,60,300,900,3600)))
 paths=materialize_exact_future_price_paths(cases,rows,(5,15,30,60,300,900,3600),8.0)
 if not paths: raise AssertionError("existing persisted history produced zero exact future price paths")
 pairs=tuple(sorted({p.pair_address for p in paths}))
 horizons=tuple(sorted({p.horizon_seconds for p in paths}))
 first=min(str(r.observed_at) for r in rows); last=max(str(r.observed_at) for r in rows)
 report={"token_address":token,"history_rows":len(rows),"first_observed_at":first,"last_observed_at":last,
 "pairs":pairs,"supported_horizons":horizons,"paths":len(paths),
 "mfe_min":min(p.mfe for p in paths),"mfe_max":max(p.mfe for p in paths),
 "mae_min":min(p.mae for p in paths),"mae_max":max(p.mae for p in paths),
 "sample_observation_ids":paths[0].evidence_observation_ids[:12],
 "read_only":True,"execution_authority":False}
 return report
