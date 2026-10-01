from __future__ import annotations
import json
from pathlib import Path
LED="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"
FRI="runtime_state/solana_opportunities/solana_scanner/phase8_physical_friction_linkage.json"
CHK="runtime_state/solana_opportunities/solana_scanner/phase8_updated_learning_coverage_checkpoint.json"
def run(root):
 root=Path(root);led=json.loads((root/LED).read_text(encoding="utf-8"));fri=json.loads((root/FRI).read_text(encoding="utf-8"));chk=json.loads((root/CHK).read_text(encoding="utf-8"))
 fam={}
 for x in led.get("cases",[]):fam[x["family"]]=fam.get(x["family"],0)+1
 supported=set(fri.get("friction_supported_families") or [])
 rows=[{"family":f,"prospective_oos_cases":n,"physical_friction_supported":f in supported,
        "gap":None if f in supported else "NO_MATCHING_PHASE7_STRICT_EXECUTABLE_FRICTION"} for f,n in sorted(fam.items())]
 return {"revision":"USLS_162E","prospective_oos_case_count":len(led.get("cases",[])),
  "phase8_family_ready_count":chk.get("family_ready_count"),"friction_supported_case_count":fri.get("friction_supported_case_count"),
  "families":rows,"net_expectancy_ready":bool(fri.get("friction_supported_case_count")),
  "next_boundary":"CLOSE_PUMP_FUN_DIRECT_DECODER_AND_CAPTURE_PUMPSWAP_OOS_OR_EXPAND_PHASE7_FRICTION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_friction_coverage_checkpoint.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
