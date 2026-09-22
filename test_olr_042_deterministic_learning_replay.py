import unittest
from qseries_v2.oracle_learning_runtime.olr_042_deterministic_learning_replay import *

class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_olr_042_deterministic_learning_replay())
    def test_order_independent(self):
        a=replay_learning_records(({"x":1},{"x":2}))
        b=replay_learning_records(({"x":2},{"x":1}))
        self.assertEqual(a.replay_hash,b.replay_hash)

if __name__=="__main__":
    print("="*72);print(" OLR-042 CERTIFICATION TEST");print(" DETERMINISTIC LEARNING REPLAY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Deterministic replay hashing certified")
    print("[DONE] OLR-042 CERTIFIED")
