from __future__ import annotations
import json
from pathlib import Path
VENUES=("MOONIT","BOOP_FUN","HEAVEN")
def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 c=json.loads((b/"remaining_venue_exact_trade_census.json").read_text(encoding="utf-8"))
 r=json.loads((b/"remaining_venue_exact_account_roles.json").read_text(encoding="utf-8"))
 t=json.loads((b/"remaining_venue_parent_transfer_evidence.json").read_text(encoding="utf-8"))
 matrix={}
 for v in VENUES:
  trades=int(c["venue_exact_counts"].get(v,0));roles=int(r["venue_exact_role_counts"].get(v,0));trs=int(t["venue_transfer_rows"].get(v,0))
  status="SEMANTICS_ROLES_TRANSFERS_READY_FOR_EXACT_ECONOMIC_RECONCILIATION" if trades and roles and trs else "PHYSICAL_EVIDENCE_INCOMPLETE"
  matrix[v]={"exact_trade_instructions":trades,"exact_account_roles":roles,"rows_with_parent_transfer_evidence":trs,"status":status}
 return {"revision":"USLS_094","matrix":matrix,"phase4_status":"IN_PROGRESS",
  "next_boundary":"MOONIT_BOOP_HEAVEN_EXACT_INSTRUCTION_ECONOMIC_RECONCILIATION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/remaining_venue_semantic_matrix.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
