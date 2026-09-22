import unittest
from qseries_v2.oracle_scientific_reasoning.osr_021_strategic_agent_incentives import *
class T(unittest.TestCase):
 def test_verifier(self): self.assertTrue(verify_osr_021_strategic_agent_incentive_reasoning())
 def test_constraint(self):
  a=StrategicAgent("a",(),(),("x",)); self.assertLess(assess_incentive(a,"x",2,0,2).incentive_score,assess_incentive(a,"x",2,0,0).incentive_score)
 def test_unavailable(self):
  with self.assertRaises(ValueError): assess_incentive(StrategicAgent("a",(),(),("x",)),"y",1,0)
if __name__=="__main__":
 print("="*72);print(" OSR-021 CERTIFICATION TEST");print(" STRATEGIC AGENT + INCENTIVE REASONING");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] Strategic-agent incentive reasoning certified");print("[DONE] OSR-021 CERTIFIED")
