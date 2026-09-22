import unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_065_outcome_calibration_bridge_readiness as m
class T(unittest.TestCase):
 def test_contract(self):
  x=m.read_latest_outcome_calibration_bridge_readiness();self.assertTrue(x)
  self.assertFalse(x["outcome_source_bound"]);self.assertFalse(x["probability_enabled"])
  self.assertEqual(tuple(x["required_outcome_fields"]),m.REQUIRED_OUTCOME_FIELDS)
if __name__=="__main__":
 print("="*88);print(" OIAR-065 CERTIFICATION TEST\n OUTCOME CALIBRATION BRIDGE READINESS");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] outcome calibration bridge readiness certified");print("[PASS] probability remains gated");print("[DONE] OIAR-065 CERTIFIED")
