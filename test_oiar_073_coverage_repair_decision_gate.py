import unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_073_coverage_repair_decision_gate as m

class T(unittest.TestCase):
 def test_contract(self):
  self.assertTrue(m.verify_oiar_073())

 def test_physical(self):
  x=m.physical_probe()
  self.assertGreater(x["sample_size"],0)
  self.assertTrue(x["active_only_normal_coverage"])
  self.assertTrue(x["explicit_missing_live_evidence_lineage"])
  self.assertTrue(x["historical_learning_requires_pre_settlement_evidence"])
  self.assertTrue(x["historical_learning_rejects_post_outcome_leakage"])
  self.assertTrue(x["historical_evidence_fabrication_forbidden"])
  self.assertTrue(x["decision"])
  self.assertTrue(x["next_pavement"])
  self.assertFalse(x["probability_enabled"])
  self.assertFalse(x["execution_authority"])

if __name__=="__main__":
 print("="*88)
 print(" OIAR-073 CERTIFICATION TEST")
 print(" CURRENT RECOVERY CONTRACT COVERAGE REPAIR DECISION GATE")
 print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] current certified OIAR-072 contract consumed")
 print("[PASS] upstream coverage decision physically classified")
 print("[PASS] historical evidence fabrication remains forbidden")
 print("[PASS] probability_enabled=FALSE")
 print("[PASS] execution_authority=FALSE")
 print("[DONE] OIAR-073 CERTIFIED")
