import tempfile,unittest,json
from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_olr_016_production_learned_state_adapter())
    def test_real_shape(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);(r/"runtime_state").mkdir()
            (r/"runtime_state"/"oracle_learning_runtime_state.json").write_text(json.dumps({"cycles":2,"outcomes_learned":3,"ocl_state":{"applied_through_sequence":3,"state_hash":"abc"}}))
            (r/"runtime_state"/"oracle_learning_event_ledger.json").write_text(json.dumps({"a":{"status":"learned","ticker":"KX"},"b":{"status":"learned","ticker":"KX"}}))
            x=load_production_learned_state(r)
            self.assertEqual(x.learned_market_counts,(("KX",2),))

if __name__=="__main__":
    print("="*72);print(" OLR-016 CERTIFICATION TEST");print(" PRODUCTION LEARNED-STATE ADAPTER");print("="*72)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not result.wasSuccessful():raise SystemExit(1)
    print("[PASS] Durable OLR state + ledger read adapter certified")
    print("[DONE] OLR-016 CERTIFIED")
