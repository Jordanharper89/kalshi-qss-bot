
from pathlib import Path
import importlib,inspect
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002_physical_exact_future_price_path_materialization import materialize_exact_future_price_paths
CANDIDATES=(
"qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence",
"qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows",
"qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate",
)
KEYS=("read","history","record","snapshot","window","persist","observation")
def audit_interfaces():
 out=[]
 for modname in CANDIDATES:
  m=importlib.import_module(modname)
  funcs=[]
  for name,obj in inspect.getmembers(m,inspect.isfunction):
   if obj.__module__==modname and any(k in name.lower() for k in KEYS):
    try:sig=str(inspect.signature(obj))
    except Exception:sig="?"
    funcs.append((name,sig))
  out.append((modname,tuple(funcs)))
 return tuple(out)
def run_gate():
 interfaces=audit_interfaces()
 print("[REAL_HISTORY_INTERFACES]")
 for mod,funcs in interfaces:
  print("[MODULE]",mod)
  for f in funcs: print("[FUNCTION]",f)
 readers=[]
 for mod,funcs in interfaces:
  for name,sig in funcs:
   if any(k in name.lower() for k in ("read","history","record","window")):
    readers.append((mod,name,sig))
 return {"interfaces":interfaces,"candidate_readers":tuple(readers),
         "exact_materializer":materialize_exact_future_price_paths.__name__,
         "production_history_reader_found":bool(readers),
         "read_only":True,"execution_authority":False}
