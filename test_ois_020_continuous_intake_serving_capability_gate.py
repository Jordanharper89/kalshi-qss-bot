import unittest
from qseries_v2.oracle_intelligence_state.ois_020_intake_serving_gate import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ois_020_continuous_intake_serving_capability_gate())
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[DONE] OIS-020 CERTIFIED")
