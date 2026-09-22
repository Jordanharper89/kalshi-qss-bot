import unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_058_deterministic_market_thesis_signature as m
class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(m.OIAR_058_BUILD_ID,"OIAR-058")
    def test_no_fake_probability(self):
        x=m.read_latest_deterministic_market_thesis_signatures();self.assertTrue(x);self.assertGreater(x["market_count"],0)
        self.assertTrue(all(v["probability"] is None for v in x["markets"]))
        self.assertTrue(x["probabilities_forbidden_without_outcome_calibration"])
if __name__=="__main__":
    print("="*88);print(" OIAR-058 CERTIFICATION TEST");print(" DETERMINISTIC MARKET THESIS SIGNATURE");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] deterministic thesis signatures certified");print("[PASS] unsupported probabilities prohibited");print("[DONE] OIAR-058 CERTIFIED")
