from __future__ import annotations
import json
from pathlib import Path
GAP="runtime_state/solana_opportunities/solana_scanner/phase8_universal_coverage_sample_gap_matrix.json"
LEARN="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_empirical_learning.json"
LEDGER="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"

def run(root):
 root=Path(root);g=json.loads((root/GAP).read_text(encoding="utf-8"))
 l=json.loads((root/LEARN).read_text(encoding="utf-8"));d=json.loads((root/LEDGER).read_text(encoding="utf-8"))
 ready=g["family_ready_count"];cases=d["case_count"];groups=l["learned_group_count"]
 complete=(ready==14 and cases>=70 and groups>0)
 return {"revision":"USLS_161T","phase8_status":"PHYSICALLY_CERTIFIED" if complete else "IN_PROGRESS",
  "universal_phase8_complete":complete,"family_ready_count":ready,"target_family_count":14,
  "prospective_oos_case_count":cases,"learned_group_count":groups,
  "certification_requirements":{"all_14_families_ready":ready==14,
   "minimum_5_cases_each_implied_by_family_gate":ready==14,"minimum_total_cases_70":cases>=70,
   "empirical_learning_nonempty":groups>0},
  "next_boundary":("PHASE9_CROSS_VENUE_LIFECYCLE_INTELLIGENCE" if complete else
   "ACCUMULATE_OOS_AND_REPAIR_ONLY_FAMILIES_MARKED_MISSING_BY_USLS_161S"),
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_prospective_learning_checkpoint.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
