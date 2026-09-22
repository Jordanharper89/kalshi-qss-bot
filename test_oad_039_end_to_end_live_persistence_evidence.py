import unittest
from qseries_v2.oracle_adapters.kalshi.oad_039_live_persistence_evidence import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_039_end_to_end_live_persistence_evidence())
    def test_mismatch(self): self.assertFalse(build_live_persistence_evidence(("a",),2).complete)
if __name__=="__main__":
    print("="*72);print(" OAD-039 CERTIFICATION TEST");print(" END-TO-END LIVE PERSISTENCE EVIDENCE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Live event-to-persistence evidence contract certified");print("[DONE] OAD-039 CERTIFIED")
