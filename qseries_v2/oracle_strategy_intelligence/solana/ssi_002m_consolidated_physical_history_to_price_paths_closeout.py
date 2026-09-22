
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate import activate_and_verify_temporal_history
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import build_outcome_pending_solana_cases
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002_physical_exact_future_price_path_materialization import materialize_exact_future_price_paths
H=(5,15,30,60,300)
def _rolling_cases(rows):
 out={}; ordered=tuple(rows)
 for n in range(2,len(ordered)):
  frozen=ordered[:n]
  for c in build_outcome_pending_solana_cases(frozen,horizons=H):
   out[(c.experience_id,c.horizon_seconds)]=c
 return tuple(out.values())
def closeout(root=None,cycles=75):
 root=Path(root or Path.cwd()).resolve()
 print("[PHASE-1] activating certified pinned temporal history")
 a=activate_and_verify_temporal_history(root=root,cycles=max(75,int(cycles)),acquisition_seconds=5.0,
  acquisition_timeout_seconds=20.0,persistence_timeout_seconds=45.0,progress=print)
 print("[ACTIVATION]",a)
 if a.successful_cycles < 75: raise AssertionError("certified acquisition did not complete 75 successful cycles")
 token=str(a.token_address);rows=tuple(read_pinned_pool_history(token,root=root,limit=4096))
 print("[PHASE-2]",{"token":token,"history_rows":len(rows),"first":str(rows[0].observed_at) if rows else None,
  "last":str(rows[-1].observed_at) if rows else None})
 if len(rows)<2: raise AssertionError("durable pinned history did not accumulate")
 cases=_rolling_cases(rows)
 print("[PHASE-3]",{"rolling_frozen_cases":len(cases)})
 if not cases: raise AssertionError("rolling pre-outcome prefixes produced no cases")
 paths=materialize_exact_future_price_paths(cases,rows,H,8.0)
 byh={h:sum(1 for p in paths if p.horizon_seconds==h) for h in H}
 print("[PHASE-4]",{"paths":len(paths),"by_horizon":byh})
 if not paths: raise AssertionError("no exact future price paths materialized")
 r={"token":token,"history_rows":len(rows),"cases":len(cases),"paths":len(paths),"by_horizon":byh,
  "pairs":tuple(sorted({p.pair_address for p in paths})),"mfe_min":min(p.mfe for p in paths),
  "mfe_max":max(p.mfe for p in paths),"mae_min":min(p.mae for p in paths),"mae_max":max(p.mae for p in paths),
  "return_min":min(p.return_fraction for p in paths),"return_max":max(p.return_fraction for p in paths),
  "sample_lineage":paths[0].evidence_observation_ids[:12],"read_only":True,"execution_authority":False}
 print("[SSI-002-PHYSICAL-CERTIFIED]",r);return r
