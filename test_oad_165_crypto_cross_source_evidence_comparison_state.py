import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_165_crypto_cross_source_evidence_comparison_state import build_crypto_evidence_comparison_states

class T(unittest.TestCase):
    def test_finalized_chain_window(self):
        a=SimpleNamespace(
            asset="BTC",market_observations=(1,),chain_observations=(2,),
            observation_time_span_seconds=900.0,evidence_comparison_possible=True,
            market_source_present=True,chain_source_present=True
        )
        r=build_crypto_evidence_comparison_states((a,))[0]
        print("[STATE]",r.state)
        print("[SPAN]",r.observation_time_span_seconds)
        self.assertTrue(r.ready_for_evidence_comparison)
        self.assertFalse(r.ready_for_prediction)
        self.assertIsNone(r.direction); self.assertIsNone(r.probability)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-165 finalized-chain comparison window certified")
