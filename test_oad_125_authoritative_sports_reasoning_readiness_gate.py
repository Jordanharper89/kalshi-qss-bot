import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_125_authoritative_sports_reasoning_readiness_gate import evaluate_sports_reasoning_readiness

class T(unittest.TestCase):
    def test_ready_for_comparison_not_prediction(self):
        x=SimpleNamespace(market_id="KX1",independent_evidence_count=1,independent_source_ids=("source.independent.mlb:game:1",))
        r=evaluate_sports_reasoning_readiness((x,))[0]
        print("[STATE]",r.state)
        print("[READY_FOR_EVIDENCE_COMPARISON]",r.ready_for_evidence_comparison)
        print("[READY_FOR_PREDICTION]",r.ready_for_prediction)
        self.assertTrue(r.ready_for_evidence_comparison)
        self.assertFalse(r.ready_for_prediction)
        self.assertIsNone(r.direction)
        self.assertIsNone(r.probability)
        self.assertFalse(r.execution_authority)

if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-125 sports reasoning readiness gate certified")
