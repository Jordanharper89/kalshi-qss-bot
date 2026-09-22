from __future__ import annotations
import json
from qseries_v2.oracle_adapters.independent.oad_353_solana_final_verified_economic_program_expansion import identify_final_verified_program

def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 d=json.loads((b/"native_instruction_stack_binding.json").read_text(encoding="utf-8"));out=[]
 for row in d.get("rows",[]):
  ev=[]
  for x in row.get("birth_instruction_events",[]):
   pid=x.get("program_id");ident=identify_final_verified_program(pid) if pid else None
   ev.append({"program_id":pid,"instruction":x.get("instruction"),
    "program_name":getattr(ident,"name",None),"program_category":getattr(ident,"category",None),
    "known":bool(getattr(ident,"known",False)) if ident else False,
    "market_relevant":bool(getattr(ident,"market_relevant",False)) if ident else False})
  exact=bool(ev) and any(x["known"] and x["market_relevant"] for x in ev)
  out.append({"slot":row.get("slot"),"signature":row.get("signature"),
   "birth_events":ev,"exact_native_pool_birth_verified":exact})
 return {"revision":"SULS_024","verified_birth_count":sum(x["exact_native_pool_birth_verified"] for x in out),
  "births":out,"execution_authority":False,"read_only":True,
  "scope":"Exact program+instruction native birth verification; pool/token account roles remain unresolved"}

def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/physical_exact_native_pool_birth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
