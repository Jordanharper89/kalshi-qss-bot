import unittest
from qseries_v2.oracle_intelligence_state.ois_006_state_update import IntelligenceStateUpdate
from qseries_v2.oracle_intelligence_state.ois_007_state_versioning import build_state_version
from qseries_v2.oracle_intelligence_state.ois_008_postgresql_boundary import *
class T(unittest.TestCase):
 def version(self):return build_state_version(IntelligenceStateUpdate("a"*64,"b"*64,"x",True,1,"c"*64))
 def test_verifier(self):self.assertTrue(verify_ois_008_postgresql_persistence_boundary())
 def test_no_io(self):self.assertFalse(build_postgresql_persistence_plan(self.version()).network_io)
 def test_record(self):self.assertEqual(materialize_postgresql_record(build_postgresql_persistence_plan(self.version())).subject_id,"x")
if __name__=="__main__":
 print("="*72);print(" OIS-008 CERTIFICATION TEST");print(" POSTGRESQL INTELLIGENCE STATE PERSISTENCE BOUNDARY");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] PostgreSQL persistence contract certified without installer/test network IO");print("[DONE] OIS-008 CERTIFIED")
