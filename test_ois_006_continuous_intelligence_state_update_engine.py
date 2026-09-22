import unittest
from qseries_v2.oracle_intelligence_state.ois_002_osr_intake_boundary import build_osr_state_intake
from qseries_v2.oracle_intelligence_state.ois_003_canonical_state import assemble_canonical_intelligence_state
from qseries_v2.oracle_intelligence_state.ois_006_state_update import *
class T(unittest.TestCase):
 def state(self,h):return assemble_canonical_intelligence_state(build_osr_state_intake("x","supported",.8,.9,.1,False,h*64),"b"*64)
 def test_verifier(self):self.assertTrue(verify_ois_006_continuous_state_update_engine())
 def test_unchanged(self):
  a=self.state("a");self.assertFalse(apply_intelligence_state_update(a,a,1).changed)
 def test_sequence(self):
  with self.assertRaises(ValueError):apply_intelligence_state_update(self.state("a"),self.state("b"),0)
if __name__=="__main__":
 print("="*72);print(" OIS-006 CERTIFICATION TEST");print(" CONTINUOUS INTELLIGENCE STATE UPDATE ENGINE");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Deterministic continuous intelligence-state updates certified");print("[DONE] OIS-006 CERTIFIED")
