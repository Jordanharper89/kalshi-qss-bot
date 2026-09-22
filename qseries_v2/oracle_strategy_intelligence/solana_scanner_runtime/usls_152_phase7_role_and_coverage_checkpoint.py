from __future__ import annotations
import json
from pathlib import Path

def _load(root,p):
 return json.loads((Path(root)/p).read_text(encoding="utf-8"))

def run(root):
 a=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_live_program_account_roles.json")
 c=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_program_local_liquidity_candidates.json")
 r=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_program_local_reserve_reference.json")
 u=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_extended_unobserved_family_live_cohort.json")
 matched=sorted(f for f,v in a.get("family_support",{}).items() if v.get("with_changed_program_accounts",0)>0)
 cand=sorted(f for f,v in c.get("family_support",{}).items() if v.get("with_candidate",0)>0)
 refs=sorted(f for f,v in r.get("family_support",{}).items() if v.get("with_reference",0)>0)
 return {"revision":"USLS_152","phase":7,
  "program_account_match_families":matched,
  "program_local_liquidity_candidate_families":cand,
  "program_local_reserve_reference_families":refs,
  "newly_observed_target_families":sorted(u.get("target_family_counts",{})),
  "still_unobserved_target_families":u.get("missing_target_families",[]),
  "phase7_status":"IN_PROGRESS","phase7_physically_certified":False,
  "remaining_required_capability":
   "CERTIFY_PROTOCOL_SPECIFIC_VAULT_AND_FEE_SEMANTICS_FOR_PROGRAM_LOCAL_CANDIDATES_THEN_EXPAND_EXECUTABLE_READY_COVERAGE",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_role_and_coverage_checkpoint.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
