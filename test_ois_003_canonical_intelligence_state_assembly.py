import unittest
from qseries_v2.oracle_intelligence_state.ois_002_osr_intake_boundary import build_osr_state_intake
from qseries_v2.oracle_intelligence_state.ois_003_canonical_state import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_003_canonical_intelligence_state_assembly())

    def test_terminal_independent(self):
        x=assemble_canonical_intelligence_state(
            build_osr_state_intake("x","uncertain",.5,.5,.2,True,"a"*64),
            "b"*64,
        )
        self.assertFalse(x.terminal_dependency)

    def test_deterministic(self):
        i=build_osr_state_intake("x","supported",.8,.9,.1,False,"a"*64)
        self.assertEqual(
            assemble_canonical_intelligence_state(i,"b"*64).canonical_hash,
            assemble_canonical_intelligence_state(i,"b"*64).canonical_hash,
        )

if __name__=="__main__":
    print("="*72);print(" OIS-003 CERTIFICATION TEST");print(" CANONICAL INTELLIGENCE STATE ASSEMBLY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Canonical terminal-independent Oracle intelligence-state assembly certified")
    print("[DONE] OIS-003 CERTIFIED")
