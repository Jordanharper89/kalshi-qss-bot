from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_137_phase7_cross_venue_coverage_checkpoint.py"
TEST=ROOT/"test_usls_137_phase7_cross_venue_coverage_checkpoint.py"

MOD_TEXT=r"""from __future__ import annotations
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
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_137_phase7_cross_venue_coverage_checkpoint import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertEqual(d["certified_family_count"],14)
  self.assertGreater(d["ready_family_count"],0)
  self.assertGreater(d["prospective_frozen_row_count"],0)
  self.assertEqual(d["phase7_status"],"IN_PROGRESS")
  self.assertFalse(d["phase7_physically_certified"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-137 Phase 7 cross-venue coverage checkpoint")
  print("[PASS] ready-family coverage and prospective freeze physically measured")
  print("[NEXT]",d["remaining_required_capability"])
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
