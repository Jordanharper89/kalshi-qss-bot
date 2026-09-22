from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_154_phase8_launch_case_materializer.py"
TEST=ROOT/"test_usls_154_phase8_launch_case_materializer.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

PATHS="runtime_state/solana_opportunities/solana_scanner/cross_venue_continuous_price_paths_repaired.json"

def run(root):
 root=Path(root)
 d=json.loads((root/PATHS).read_text(encoding="utf-8"))
 rows=[]
 for i,x in enumerate(d.get("paths",[])):
  first=x.get("first_price");last=x.get("last_price")
  if first in (None,0) or last is None:continue
  rows.append({
   "case_id":f"USLS154-{i:06d}",
   "family":x.get("family"),"market_address":x.get("market_address"),
   "asset_a":x.get("asset_a"),"asset_b":x.get("asset_b"),
   "trade_count":x.get("trade_count",0),
   "first_price":first,"last_price":last,
   "high_price":x.get("high_price"),"low_price":x.get("low_price"),
   "mfe":x.get("mfe"),"mae":x.get("mae"),
   "volume_base":x.get("volume_base"),"volume_quote":x.get("volume_quote"),
   "checkpoint_count":len(x.get("checkpoints") or []),
   "price_path_count":len(x.get("price_path") or []),
   "observational_return":float(last)/float(first)-1,
   "execution_supported":False,
   "execution_authority":False})
 by={}
 for x in rows:by[x["family"]]=by.get(x["family"],0)+1
 return {"revision":"USLS_154","case_count":len(rows),"family_case_counts":by,
  "cases":rows,"case_semantics":"OBSERVATIONAL_CROSS_LAUNCH_CASES_NOT_EXECUTABLE_PNL",
  "next_boundary":"LEAKAGE_SAFE_FEATURE_SNAPSHOT_EXTRACTION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_launch_cases.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_154_phase8_launch_case_materializer import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"case_count":d["case_count"],
   "family_case_counts":d["family_case_counts"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["case_count"],0,"NO_PHASE8_LAUNCH_CASES")
  self.assertEqual(len(d["family_case_counts"]),14)
  self.assertEqual(d["case_semantics"],"OBSERVATIONAL_CROSS_LAUNCH_CASES_NOT_EXECUTABLE_PNL")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-154 Phase 8 launch-case materializer")
  print("[PASS] all 14 certified venue families represented as observational learning cases")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8"); TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT)); print("[PASS] test:",TEST.name); print("[PASS] execution_authority=FALSE")
