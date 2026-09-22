import unittest
from qseries_v2.oracle_intelligence_state.ois_002_osr_intake_boundary import build_osr_state_intake
from qseries_v2.oracle_intelligence_state.ois_003_canonical_state import assemble_canonical_intelligence_state
from qseries_v2.oracle_intelligence_state.ois_004_query_snapshot import *

class T(unittest.TestCase):
    def state(self,subject):
        return assemble_canonical_intelligence_state(
            build_osr_state_intake(subject,"supported",.8,.9,.1,False,"a"*64),
            "b"*64,
        )

    def test_verifier(self):
        self.assertTrue(verify_ois_004_read_only_query_snapshot())

    def test_query_missing(self):
        self.assertIsNone(query_intelligence_state(build_intelligence_state_snapshot((self.state("a"),)),"b"))

    def test_deterministic(self):
        a=self.state("a");b=self.state("b")
        self.assertEqual(
            build_intelligence_state_snapshot((a,b)).snapshot_hash,
            build_intelligence_state_snapshot((b,a)).snapshot_hash,
        )

if __name__=="__main__":
    print("="*72);print(" OIS-004 CERTIFICATION TEST");print(" READ-ONLY QUERY SNAPSHOT");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic Terminal/API-safe intelligence-state snapshot certified")
    print("[DONE] OIS-004 CERTIFIED")
