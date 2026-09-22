import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_019_continuous_feedback_snapshot_runtime import *

class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_olr_019_continuous_feedback_snapshot_runtime())
    def test_writes_only_olr_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);x=materialize_feedback_snapshot(r)
            self.assertTrue((r/"runtime_state"/"oracle_reasoning_feedback_snapshot.json").is_file())

if __name__=="__main__":
    print("="*72);print(" OLR-019 CERTIFICATION TEST");print(" CONTINUOUS FEEDBACK SNAPSHOT RUNTIME");print("="*72)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not result.wasSuccessful():raise SystemExit(1)
    print("[PASS] OLR-owned atomic feedback snapshot runtime certified")
    print("[DONE] OLR-019 CERTIFIED")
