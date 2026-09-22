import unittest
from qseries_v2.oracle_intelligence_state.ois_006_state_update import IntelligenceStateUpdate
from qseries_v2.oracle_intelligence_state.ois_007_state_versioning import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ois_007_state_versioning_transition_lineage())
 def test_chain(self):
  u1=IntelligenceStateUpdate("a"*64,"b"*64,"x",True,1,"c"*64);v1=build_state_version(u1)
  u2=IntelligenceStateUpdate("b"*64,"d"*64,"x",True,2,"e"*64);v2=build_state_version(u2,v1)
  self.assertEqual(v2.version,2);self.assertEqual(v2.parent_state_hash,"b"*64)
 def test_parent_mismatch(self):
  v=build_state_version(IntelligenceStateUpdate("a"*64,"b"*64,"x",True,1,"c"*64))
  with self.assertRaises(ValueError):build_state_version(IntelligenceStateUpdate("z"*64,"d"*64,"x",True,2,"e"*64),v)
if __name__=="__main__":
 print("="*72);print(" OIS-007 CERTIFICATION TEST");print(" STATE VERSIONING + TRANSITION LINEAGE");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Append-only state versioning and transition lineage certified");print("[DONE] OIS-007 CERTIFIED")
