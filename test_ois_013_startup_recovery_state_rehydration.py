import unittest
from qseries_v2.oracle_intelligence_state.ois_013_startup_recovery import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ois_013_startup_recovery_state_rehydration())
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[DONE] OIS-013 CERTIFIED")
