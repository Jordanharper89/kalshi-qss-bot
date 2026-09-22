import unittest
from qseries_v2.oracle_intelligence_state.ois_046_runtime_state import build_oracle_live_runtime_state
from qseries_v2.oracle_intelligence_state.ois_047_runtime_activation import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_047_oracle_live_runtime_activation_controller())

    def test_invalid_transition(self):
        s=build_oracle_live_runtime_state("STOPPED",0,False,False)
        with self.assertRaises(ValueError):
            transition_runtime(s,"RUNNING",True,True)

    def test_sequence_advances(self):
        s=build_oracle_live_runtime_state("STOPPED",0,False,False)
        self.assertEqual(transition_runtime(s,"STARTING",False,False).sequence,1)

if __name__=="__main__":
    print("="*72);print(" OIS-047 CERTIFICATION TEST");print(" ORACLE LIVE RUNTIME ACTIVATION CONTROLLER");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Oracle Live Runtime activation transitions certified")
    print("[DONE] OIS-047 CERTIFIED")
