from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_353_solana_final_verified_economic_program_expansion import identify_final_verified_program

def verify(root):
 src=root/"runtime_state/solana_opportunities/launch_surveillance/native_birth_candidate_physical_gate.json"
 d=json.loads(src.read_text(encoding="utf-8"))
 rows=[]
 for c in d.get("candidates",[]):
  ids=[]
  for pid in c.get("program_ids",[]):
   x=identify_final_verified_program(pid)
   ids.append({"program_id":pid,"name":getattr(x,"name",None),"category":getattr(x,"category",None),
    "known":bool(getattr(x,"known",False)),"market_relevant":bool(getattr(x,"market_relevant",False)),
    "evidence_class":getattr(x,"evidence_class",None)})
  logs="\n".join(c.get("logs") or []).lower()
  init=any(x in logs for x in ("initializepool","initialize_pool","initialize pool","initializepoolwithdynamicconfig"))
  create="create pool" in logs
  relevant=any(x["known"] and x["market_relevant"] for x in ids)
  rows.append({"slot":c.get("slot"),"signature":c.get("signature"),"program_identities":ids,
   "create_pool_log":create,"initialize_pool_log":init,"market_relevant_program":relevant,
   "instruction_level_birth_candidate":bool(create and init and relevant),"execution_authority":False})
 return {"revision":"SULS_021","verified_candidates":rows,
  "instruction_level_candidates":sum(x["instruction_level_birth_candidate"] for x in rows),
  "execution_authority":False,"read_only":True}

def write(root):
 d=verify(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/exact_program_instruction_birth_verification.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
