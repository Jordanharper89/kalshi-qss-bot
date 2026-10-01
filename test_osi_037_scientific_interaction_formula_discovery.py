import unittest
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_037_scientific_interaction_formula_discovery import discover
class T(unittest.TestCase):
 def test_formula(self):
  cases=[]
  for i in range(8):
   cases.append({"features":{"liquidity":1,"swap_velocity":1,"smart_money_flow":1},
                 "outcomes":{"60":.10 if i<6 else -.05}})
  m={"feature_names":["liquidity","swap_velocity","smart_money_flow"],"comparable_cases":cases}
  d=discover(m,"60",5,3);self.assertGreater(d["candidate_count"],0);self.assertFalse(d["raw_frequency_is_calibrated_probability"])
  print("[TOP_FORMULA]",d["candidates"][0]["formula"]);print("[SAMPLE]",d["candidates"][0]["sample_size"])
  print("[PASS] OSI-037 scientific interaction/formula discovery")
  print("[TRADER] Tests X, Y, Z and their interactions against actual historical outcomes")
  print("[PASS] raw_frequency_is_calibrated_probability=FALSE")
if __name__=="__main__":unittest.main()
