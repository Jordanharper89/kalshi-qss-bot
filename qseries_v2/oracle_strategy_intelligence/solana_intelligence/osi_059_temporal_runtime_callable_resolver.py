from __future__ import annotations
import importlib,inspect,json
from pathlib import Path
MODULES=(
 "qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence",
 "qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows",
 "qseries_v2.oracle_adapters.independent.oad_275_solana_continuous_observation_resilient_worker",
 "qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate",
)
TOKENS=("read","load","history","snapshot","record","pool","temporal","observation")
def resolve():
 out=[]
 for modname in MODULES:
  try:m=importlib.import_module(modname)
  except Exception as e:
   out.append({"module":modname,"error":repr(e),"callables":[]});continue
  rows=[]
  for name,obj in vars(m).items():
   if name.startswith("_") or not callable(obj):continue
   try:sig=str(inspect.signature(obj))
   except Exception:sig="UNKNOWN"
   score=sum(1 for t in TOKENS if t in name.lower())
   rows.append({"name":name,"signature":sig,"score":score})
  rows.sort(key=lambda x:(-x["score"],x["name"]))
  out.append({"module":modname,"error":None,"callables":rows})
 return {"revision":"OSI_059","modules":out,"execution_authority":False,"read_only":True}
def write(root):
 d=resolve();p=root/"runtime_state/solana_opportunities/temporal_runtime_callables.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
