import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_180_crypto_experience_learning_outcome_handoff_gate import evaluate_crypto_learning_handoff
from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation
class T(unittest.TestCase):
    def test_hold_then_ready(self):
        c=SimpleNamespace(experience_id="e1",asset="BTC",evidence_hash="a"*64,condition_hash="b"*64)
        l=SimpleNamespace(experience_id="e1",lineage_hash="c"*64)
        hold=evaluate_crypto_learning_handoff(c,l)
        print("[WITHOUT_OUTCOME]",hold.gate_state)
        self.assertEqual(hold.gate_state,"HOLD_OUTCOME_REQUIRED")
        o=build_outcome_observation("BTC","future_price_window",1.0,"2026-08-30T00:00:00Z","source:test","d"*64)
        ready=evaluate_crypto_learning_handoff(c,l,o)
        print("[WITH_VERIFIED_OUTCOME]",ready.gate_state)
        self.assertTrue(ready.learning_event_ready)
        self.assertEqual(len(ready.learning_event_hash),64)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-180 exact OCL outcome-required learning handoff certified")
