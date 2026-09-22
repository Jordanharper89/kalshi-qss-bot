from __future__ import annotations
import inspect,json
TARGETS=(
 "qseries_v2.oracle_adapters.independent.oad_336_solana_pump_meteora_market_behavior_decoder",
 "qseries_v2.oracle_adapters.independent.oad_355_solana_final_economic_behavior_decoder",
 "qseries_v2.oracle_adapters.independent.oad_353_solana_final_verified_economic_program_expansion",
)
def audit():
 rows=[]
 for name in TARGETS:
  try:
   m=__import__(name,fromlist=["*"]);src=inspect.getsource(m);funcs={}
   for n,v in vars(m).items():
    if callable(v) and not n.startswith("_"):
     try:funcs[n]=str(inspect.signature(v))
     except Exception:funcs[n]="?"
   rows.append({"module":name,"functions":funcs,"source_excerpt":src[:16000]})
  except Exception as e:rows.append({"module":name,"error":f"{type(e).__name__}: {e}"})
 return {"revision":"SULS_027","modules":rows,"execution_authority":False,"read_only":True}
def write(root):
 d=audit();p=root/"runtime_state/solana_opportunities/launch_surveillance/meteora_birth_decoder_contracts.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
