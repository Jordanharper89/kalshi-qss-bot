from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_116d_phase6_repaired_full_venue_coverage_gate.py"
TEST=ROOT/"test_usls_116d_phase6_repaired_full_venue_coverage_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

CERTIFIED=("PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM",
 "RAYDIUM_CPMM","METEORA_DBC","METEORA_DAMM_V1","METEORA_DAMM_V2","METEORA_DLMM",
 "ORCA","MOONIT","BOOP_FUN","HEAVEN")

def run(root):
 root=Path(root)
 econ=json.loads((root/"runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows_repaired.json").read_text(encoding="utf-8"))
 paths=json.loads((root/"runtime_state/solana_opportunities/solana_scanner/cross_venue_continuous_price_paths_repaired.json").read_text(encoding="utf-8"))
 er=econ.get("family_row_counts",{});pr=paths.get("family_path_counts",{})
 rows=[]
 for f in CERTIFIED:
  rows.append({"family":f,"economic_rows":er.get(f,0),
   "path_count":pr.get(f,0),
   "economic_covered":er.get(f,0)>0,
   "path_covered":pr.get(f,0)>0})
 missing_e=[x["family"] for x in rows if not x["economic_covered"]]
 missing_p=[x["family"] for x in rows if not x["path_covered"]]
 ok=not missing_e and not missing_p
 return {"revision":"USLS_116D","source_revision":"USLS_116B_116C",
  "certified_family_count":len(CERTIFIED),
  "economic_covered_count":sum(x["economic_covered"] for x in rows),
  "path_covered_count":sum(x["path_covered"] for x in rows),
  "families":rows,"missing_economic_families":missing_e,
  "missing_path_families":missing_p,
  "full_venue_path_coverage":ok,
  "next_boundary":"PHASE6_FINAL_CERTIFICATION" if ok else "PHASE6_REPAIR_REQUIRED",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase6_repaired_full_venue_coverage_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_116d_phase6_repaired_full_venue_coverage_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "certified_family_count","economic_covered_count","path_covered_count",
   "missing_economic_families","missing_path_families",
   "full_venue_path_coverage","next_boundary")},sort_keys=True))
  self.assertEqual(d["economic_covered_count"],d["certified_family_count"],
   "CERTIFIED_VENUE_ECONOMIC_COVERAGE_INCOMPLETE")
  self.assertEqual(d["path_covered_count"],d["certified_family_count"],
   "CERTIFIED_VENUE_PRICE_PATH_COVERAGE_INCOMPLETE")
  self.assertTrue(d["full_venue_path_coverage"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-116D Phase 6 repaired full venue coverage")
  print("[PASS] all 14 certified venue families have economic rows and price paths")
  print("[NEXT] PHASE6_FINAL_CERTIFICATION")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
