import tempfile,unittest,json
from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_036_live_feedback_read_model import *

class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_olr_036_live_feedback_read_model())
    def test_read(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);(r/"runtime_state").mkdir()
            (r/"runtime_state"/"oracle_live_reasoning_feedback.json").write_text(json.dumps({"markets":[{"market_ticker":"KX","samples":5,"mature":True}]}))
            self.assertTrue(load_live_feedback_snapshot(r)["KX"].mature)

if __name__=="__main__":
    print("="*72);print(" OLR-036 CERTIFICATION TEST");print(" LIVE FEEDBACK READ MODEL");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Read-only live calibration feedback model certified")
    print("[DONE] OLR-036 CERTIFIED")
