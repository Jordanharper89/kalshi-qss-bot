import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_195_crypto_historical_outcome_contradiction_uncertainty import build_historical_outcome_uncertainty
class T(unittest.TestCase):
    def test_uncertainty(self):
        s=SimpleNamespace(asset="BTC",horizon_seconds=60,raw_sample_size=3,effective_sample_size=2.7,
            weighted_positive_share=.5,weighted_negative_share=.5,weighted_unchanged_share=0.0)
        x=build_historical_outcome_uncertainty((s,))[0]
        print("[CONTRADICTION]",x.contradiction_ratio); print("[ENTROPY]",x.normalized_outcome_entropy); print("[EVIDENCE]",x.evidence_state)
        self.assertEqual(x.contradiction_state,"HIGH_CONTRADICTION")
        self.assertEqual(x.evidence_state,"INSUFFICIENT_EFFECTIVE_SAMPLE")
        self.assertFalse(x.probability_enabled)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-195 historical contradiction + uncertainty intelligence certified")
