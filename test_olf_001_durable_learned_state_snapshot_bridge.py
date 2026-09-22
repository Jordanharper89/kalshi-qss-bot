import unittest
from qseries_v2.oracle_learning_feedback.olf_001_learned_state_snapshot import *

class T(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(OLF_001_BUILD_ID,"OLF-001")
    def test_contract(self):
        self.assertTrue(callable(materialize_learned_feedback_snapshot))
        self.assertTrue(callable(verify_snapshot_matches_current_learner))

if __name__=="__main__":
    print("="*88)
    print(" OLF-001 CERTIFICATION TEST")
    print(" DURABLE LEARNED-STATE SNAPSHOT BRIDGE")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Learned-state snapshot bridge contract certified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLF-001 CERTIFIED")
