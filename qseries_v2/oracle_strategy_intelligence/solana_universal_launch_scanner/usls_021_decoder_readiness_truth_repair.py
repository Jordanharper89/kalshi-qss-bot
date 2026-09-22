from __future__ import annotations
import json
from pathlib import Path

TARGETS=("PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM",
"RAYDIUM_CPMM","METEORA_DBC","METEORA_DAMM","METEORA_DLMM","METEORA_DYN",
"ORCA","MOONIT","BOOP_FUN","HEAVEN")

def repair(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 old=json.loads((base/"family_birth_decoder_contracts.json").read_text(encoding="utf-8"))
 fw=json.loads((base/"exact_birth_semantic_firewall.json").read_text(encoding="utf-8"))
 old_by={x["family"]:x for x in old["rows"]}
 rows=[]
 for fam in TARGETS:
  prior=old_by.get(fam,{})
  exact_existing=(fam=="METEORA_DAMM" and prior.get("exact_pool_identity_certified") is True)
  exact_live=(fam=="PUMP_FUN" and fw.get("exact_create_v2_count",0)>0)
  exact=bool(exact_existing or exact_live)
  state="EXACT_DECODER_CERTIFIED" if exact_existing else ("READY_FOR_EXACT_ACCOUNT_MAPPING" if exact_live else "EXACT_BIRTH_NOT_YET_PROVEN")
  rows.append({"family":fam,"prior_state":prior.get("decoder_state"),"decoder_state":state,
   "exact_birth_instruction_proven":exact,"exact_pool_identity_certified":exact_existing,
   "heuristic_birth_evidence_admissible":False,"execution_authority":False})
 return {"revision":"USLS_021","rows":rows,
  "ready_count":sum(1 for x in rows if x["decoder_state"]=="READY_FOR_EXACT_ACCOUNT_MAPPING"),
  "certified_count":sum(1 for x in rows if x["decoder_state"]=="EXACT_DECODER_CERTIFIED"),
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=repair(root);p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/family_birth_decoder_contracts_exact.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
