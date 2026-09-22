import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_185_crypto_verified_learning_event_activation import activate_verified_crypto_learning_event
from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation
class T(unittest.TestCase):
    def test_activation(self):
        c=SimpleNamespace(experience_id="e1",asset="BTC",evidence_hash="a"*64,condition_hash="b"*64)
        l=SimpleNamespace(experience_id="e1",lineage_hash="c"*64)
        o=build_outcome_observation("BTC","coinbase_spot_return_60s",0.01,"2026-08-29T02:01:01Z","coinbase:BTC-USD:ticker:1","d"*64)
        f=SimpleNamespace(outcome_observation=o,source_ref="coinbase:BTC-USD:ticker:1")
        x=activate_verified_crypto_learning_event(c,l,f)
        print("[GATE]",x.gate_state)
        print("[EVENT_HASH]",x.learning_event.event_hash)
        print("[BATCH]",x.runtime_batch.start_sequence,x.runtime_batch.end_sequence)
        self.assertTrue(x.intake_ready)
        self.assertEqual(x.gate_state,"READY_FOR_OCL_LEARNING_EVENT")
        self.assertEqual((x.runtime_batch.start_sequence,x.runtime_batch.end_sequence),(1,2))
if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-185 verified OCL LearningEvent + intake batch activation certified")
