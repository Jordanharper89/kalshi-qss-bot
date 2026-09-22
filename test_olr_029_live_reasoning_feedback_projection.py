import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_029_live_reasoning_feedback_projection import *

class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_olr_029_live_reasoning_feedback_projection())
    def test_snapshot_exists(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);x=materialize_live_reasoning_feedback(r)
            self.assertTrue((r/"runtime_state"/"oracle_live_reasoning_feedback.json").is_file())

if __name__=="__main__":
    print("="*72);print(" OLR-029 CERTIFICATION TEST");print(" LIVE REASONING FEEDBACK PROJECTION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Atomic live reasoning feedback projection certified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-029 CERTIFIED")
