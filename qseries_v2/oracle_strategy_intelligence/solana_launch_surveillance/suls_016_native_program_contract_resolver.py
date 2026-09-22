from __future__ import annotations
import inspect,json
from pathlib import Path

MODULES=(
 "qseries_v2.oracle_adapters.independent.oad_333_solana_authoritative_program_identity_registry",
 "qseries_v2.oracle_adapters.independent.oad_339_solana_reconciled_program_identity_registry",
 "qseries_v2.oracle_adapters.independent.oad_343_solana_verified_recurring_program_identity_expansion",
 "qseries_v2.oracle_adapters.independent.oad_348_solana_verified_economic_program_expansion",
 "qseries_v2.oracle_adapters.independent.oad_353_solana_final_verified_economic_program_expansion",
)

def resolve():
 rows=[]
 for name in MODULES:
  try:
   m=__import__(name,fromlist=["*"])
   funcs={}
   for n,v in vars(m).items():
    if callable(v) and not n.startswith("_"):
     try: funcs[n]=str(inspect.signature(v))
     except Exception: funcs[n]="?"
   src=inspect.getsource(m)
   rows.append({"module":name,"functions":funcs,"source_excerpt":src[:12000]})
  except Exception as e:
   rows.append({"module":name,"error":f"{type(e).__name__}: {e}"})
 return {"revision":"SULS_016","modules":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=resolve();p=root/"runtime_state/solana_opportunities/launch_surveillance/native_program_contracts.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
