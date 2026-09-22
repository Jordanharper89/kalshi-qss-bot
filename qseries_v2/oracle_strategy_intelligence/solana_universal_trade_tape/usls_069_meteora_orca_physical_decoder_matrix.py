from __future__ import annotations
import json
from pathlib import Path
VENUES=("METEORA_DBC","METEORA_DAMM","METEORA_DLMM","METEORA_DYN","ORCA")

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 hyd=json.loads((base/"meteora_orca_deep_transactions.json").read_text(encoding="utf-8"))
 ix=json.loads((base/"meteora_orca_exact_swap_instructions.json").read_text(encoding="utf-8"))
 ec=json.loads((base/"meteora_orca_transfer_economic_probe.json").read_text(encoding="utf-8"))
 matrix={}
 for v in VENUES:
  h=int(hyd["hydrated_counts"].get(v,0));s=int(ix["venue_counts"].get(v,0));e=int(ec["venue_exact_counts"].get(v,0))
  if v=="METEORA_DYN":
   status="OBSERVED_SCHEMA_PENDING_OFFICIAL_VERIFICATION" if h else "NOT_OBSERVED_SCHEMA_PENDING"
  elif e>0:status="EXACT_SWAP_SIGNER_ECONOMICS_POOL_ROLE_PENDING"
  elif s>0:status="EXACT_SWAP_INSTRUCTION_ECONOMICS_PENDING"
  elif h>0:status="HYDRATED_ACTIVITY_DECODER_PENDING"
  else:status="BLOCKED_BY_NO_HYDRATABLE_LIVE_ACTIVITY"
  matrix[v]={"hydrated_transactions":h,"exact_swap_instructions":s,"exact_two_asset_signer_economics":e,"status":status}
 return {"revision":"USLS_069","matrix":matrix,"phase4_status":"IN_PROGRESS",
  "next_boundary":"METEORA_ORCA_EXACT_POOL_ROLE_AND_INSTRUCTION_ECONOMIC_RECONCILIATION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_orca_physical_decoder_matrix.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
