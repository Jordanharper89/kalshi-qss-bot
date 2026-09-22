from __future__ import annotations
import json
from pathlib import Path

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 prev=json.loads((base/"meteora_orca_reconciliation_matrix.json").read_text(encoding="utf-8"))
 v1=json.loads((base/"meteora_damm_v1_exact_economics.json").read_text(encoding="utf-8"))
 matrix=dict(prev["matrix"]);n=int(v1["exact_economic_count"])
 matrix["METEORA_DYN"]={**matrix["METEORA_DYN"],"corrected_identity":"METEORA_DAMM_V1",
  "correct_program_id":"Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB",
  "exact_instruction_transfer_economics":n,
  "status":"EXACT_DAMM_V1_INSTRUCTION_ECONOMICS_CERTIFIED" if n>0 else "DAMM_V1_REPAIR_INCOMPLETE"}
 return {"revision":"USLS_079","matrix":matrix,"phase4_status":"IN_PROGRESS",
  "damm_v1_program_id_repaired":True,
  "next_boundary":"DBC_SOURCE_ROLE_CERTIFICATION_PLUS_MULTI_VENUE_UNIVERSAL_NORMALIZATION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_orca_reconciliation_matrix.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
