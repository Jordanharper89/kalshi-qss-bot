from __future__ import annotations
import json
from pathlib import Path
VENUES=("METEORA_DBC","METEORA_DAMM","METEORA_DLMM","METEORA_DYN","ORCA")

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 m=json.loads((base/"meteora_orca_physical_decoder_matrix.json").read_text(encoding="utf-8"))
 r=json.loads((base/"meteora_orca_exact_transfer_reconciliation.json").read_text(encoding="utf-8"))
 d=json.loads((base/"meteora_dbc_physical_role_discovery.json").read_text(encoding="utf-8"))
 out={}
 for v in VENUES:
  prev=m["matrix"][v];exact=int(r["venue_exact_counts"].get(v,0))
  if v=="METEORA_DBC":
   status="PHYSICAL_ROLE_DISCOVERY_PENDING_SOURCE_CERTIFICATION"
  elif v=="METEORA_DYN":
   status=prev["status"]
  elif exact>0:
   status="EXACT_INSTRUCTION_TRANSFER_ECONOMICS_POOL_ROLE_CERTIFIED_OR_PARTIAL"
  elif prev["exact_swap_instructions"]>0:
   status="EXACT_SWAP_INSTRUCTION_TRANSFER_RECONCILIATION_PENDING"
  else:status=prev["status"]
  out[v]={**prev,"exact_instruction_transfer_economics":exact,"status":status}
 return {"revision":"USLS_074","matrix":out,"dbc_role_certified":d["role_certified"],
  "phase4_status":"IN_PROGRESS","next_boundary":"DBC_SOURCE_ROLE_CERTIFICATION_PLUS_DAMM_DLMM_ORCA_EXACT_NORMALIZATION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_orca_reconciliation_matrix.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
