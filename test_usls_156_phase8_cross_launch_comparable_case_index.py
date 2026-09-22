import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_156_phase8_cross_launch_comparable_case_index import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  multi=sum(x["family_count"]>1 for x in d["groups"])
  print("[STATE]",json.dumps({"comparable_group_count":d["comparable_group_count"],
   "cross_family_group_count":multi,"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["comparable_group_count"],0)
  self.assertTrue(all(x["calibrated_probability"] is None for x in d["groups"]))
  self.assertIn("NOT_CALIBRATED_PROBABILITY",d["probability_semantics"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-156 cross-launch comparable-case index")
  print("[PASS] raw empirical frequencies kept separate from calibrated probability")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
