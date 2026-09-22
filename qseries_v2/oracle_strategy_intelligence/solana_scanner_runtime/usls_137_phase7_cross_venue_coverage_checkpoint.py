from __future__ import annotations
import json
from pathlib import Path

FAMILIES=("PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM",
 "RAYDIUM_CPMM","METEORA_DBC","METEORA_DAMM_V1","METEORA_DAMM_V2","METEORA_DLMM",
 "ORCA","MOONIT","BOOP_FUN","HEAVEN")

def _load(root,name):
 return json.loads((Path(root)/name).read_text(encoding="utf-8"))

def run(root):
 gap=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_cross_venue_executable_gap_matrix.json")
 cand=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_cross_venue_executable_candidates.json")
 frz=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_prospective_executable_freeze.json")
 ready=cand.get("family_readiness",{})
 coverage={f:ready.get(f,{}).get("ready",0) for f in FAMILIES}
 missing=[f for f,v in coverage.items() if v<=0]
 all_ready=not missing
 return {"revision":"USLS_137","phase":7,
  "certified_family_count":14,
  "ready_family_count":sum(v>0 for v in coverage.values()),
  "ready_rows_by_family":coverage,
  "missing_ready_families":missing,
  "prospective_frozen_row_count":frz.get("frozen_row_count",0),
  "phase7_physically_certified":False,
  "phase7_status":"IN_PROGRESS",
  "remaining_required_capability":(
   "PROSPECTIVE_OUTCOME_COLLECTION_AND_NET_EXECUTABLE_VALIDATION"
   if all_ready else
   "CLOSE_EXECUTABLE_INPUT_GAPS_FOR_MISSING_VENUES_THEN_PROSPECTIVE_OUTCOME_VALIDATION"),
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_cross_venue_coverage_checkpoint.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
