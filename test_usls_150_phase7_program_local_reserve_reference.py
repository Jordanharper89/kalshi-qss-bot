import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_150_phase7_program_local_reserve_reference import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  n=sum(v["with_reference"] for v in d["family_support"].values())
  print("[STATE]",json.dumps({"row_count":d["row_count"],"reference_rows":n,
   "family_support":d["family_support"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(n,0,"NO_PROGRAM_LOCAL_PRE_POST_REFERENCES")
  self.assertIn("NOT_YET_CERTIFIED_POOL_LIQUIDITY",d["reference_semantics"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-150 program-local reserve reference")
  print("[PASS] pre/post balance references materialized without overclaiming certified pool liquidity")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
