import tempfile,unittest,json
from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_041_learning_health_model import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_olr_041_learning_health_model())
    def test_waiting_is_not_failure(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);(r/"runtime_state").mkdir()
            (r/"runtime_state"/"oracle_learning_runtime_state.json").write_text(json.dumps({"cycles":5,"outcomes_learned":0}))
            x=inspect_learning_health(r)
            self.assertEqual(x.health,"HEALTHY_WAITING_FOR_ELIGIBLE_OUTCOMES")

if __name__=="__main__":
    print("="*72);print(" OLR-041 CERTIFICATION TEST");print(" LEARNING HEALTH MODEL");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Healthy-zero-learning state distinguished from runtime failure")
    print("[DONE] OLR-041 CERTIFIED")
