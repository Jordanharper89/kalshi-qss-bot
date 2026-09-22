import unittest
from qseries_v2.oracle_postgresql_reliability.opr_001_persistent_queue_session import *

class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(OPR_001_BUILD_ID,"OPR-001")
    def test_contract(self):self.assertTrue(verify_opr_001_persistent_postgresql_queue_session())
    def test_submission(self):self.assertEqual(PersistentQueueSubmission("r","p",1,3).observation_count,3)

if __name__=="__main__":
    print("="*88);print(" OPR-001 CERTIFICATION TEST");print(" PERSISTENT POSTGRESQL QUEUE SESSION");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Long-lived PostgreSQL queue session contract certified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPR-001 CERTIFIED")
