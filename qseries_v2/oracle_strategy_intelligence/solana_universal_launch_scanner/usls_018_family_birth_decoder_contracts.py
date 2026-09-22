from __future__ import annotations
import json
from pathlib import Path

TARGETS=("PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM",
"RAYDIUM_CPMM","METEORA_DBC","METEORA_DAMM","METEORA_DLMM","METEORA_DYN",
"ORCA","MOONIT","BOOP_FUN","HEAVEN")

def build(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 ix=json.loads((base/"live_program_instruction_evidence.json").read_text(encoding="utf-8"))
 corr=json.loads((base/"birth_log_instruction_correlation.json").read_text(encoding="utf-8"))
 roles=json.loads((base/"token_pool_role_evidence.json").read_text(encoding="utf-8"))
 observed={x["matched_family"] for x in ix.get("rows") or []}
 birth={x["matched_family"] for x in corr.get("rows") or [] if x.get("candidate_birth_evidence")}
 role_fams={f for r in roles.get("rows") or [] if r.get("candidate_token_mints") for f in r.get("families") or []}
 rows=[]
 for fam in TARGETS:
  state=("READY_FOR_EXACT_ACCOUNT_MAPPING" if fam in observed and fam in birth and fam in role_fams
   else "LIVE_ACTIVITY_ONLY" if fam in observed else "AWAIT_LIVE_SAMPLE")
  rows.append({"family":fam,"instruction_evidence":fam in observed,"birth_log_evidence":fam in birth,
   "token_role_evidence":fam in role_fams,"decoder_state":state,
   "exact_pool_identity_certified":fam=="METEORA_DAMM",
   "execution_authority":False})
 return {"revision":"USLS_018","target_count":len(rows),
  "ready_count":sum(1 for x in rows if x["decoder_state"]=="READY_FOR_EXACT_ACCOUNT_MAPPING"),
  "rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/family_birth_decoder_contracts.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
