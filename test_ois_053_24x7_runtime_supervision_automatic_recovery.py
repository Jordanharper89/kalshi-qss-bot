import unittest
from qseries_v2.oracle_intelligence_state.ois_046_runtime_state import build_oracle_live_runtime_state
from qseries_v2.oracle_intelligence_state.ois_053_runtime_supervision import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_053_24x7_runtime_supervision_automatic_recovery())

    def test_restart_when_unrecoverable(self):
        r=build_oracle_live_runtime_state("RUNNING",1,True,True)
        self.assertTrue(supervise_runtime(r,False,False).restart_required)

    def test_healthy_continues(self):
        r=build_oracle_live_runtime_state("RUNNING",1,True,True)
        self.assertEqual(supervise_runtime(r,True,True).action,"CONTINUE")

if __name__=="__main__":
    print("="*72);print(" OIS-053 CERTIFICATION TEST");print(" 24/7 RUNTIME SUPERVISION + AUTOMATIC RECOVERY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Oracle 24/7 runtime supervision/recovery coordination certified")
    print("[DONE] OIS-053 CERTIFIED")
