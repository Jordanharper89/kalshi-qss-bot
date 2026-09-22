from __future__ import annotations
import importlib,inspect,json
from pathlib import Path
MODULE="qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution"
PREFERRED=("attribute","outcome","forward","verify","grade","resolve")
def resolve():
 m=importlib.import_module(MODULE);rows=[]
 for name,obj in vars(m).items():
  if name.startswith("_") or not callable(obj):continue
  try:sig=str(inspect.signature(obj))
  except Exception:sig="UNKNOWN"
  score=sum(1 for k in PREFERRED if k in name.lower())
  rows.append({"name":name,"signature":sig,"score":score})
 rows.sort(key=lambda x:(-x["score"],x["name"]))
 return {"revision":"OSI_056","module":MODULE,"callables":rows,"callable_count":len(rows),"execution_authority":False,"read_only":True}
def write(root):
 d=resolve();p=root/"runtime_state/solana_opportunities/oad314_runtime_callables.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
