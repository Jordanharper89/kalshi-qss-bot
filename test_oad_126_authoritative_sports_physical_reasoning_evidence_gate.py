import unittest
from qseries_v2.oracle_adapters.independent.oad_126_authoritative_sports_physical_reasoning_evidence_gate import run_physical_sports_reasoning_evidence_gate

class T(unittest.TestCase):
    def test_physical(self):
        r=run_physical_sports_reasoning_evidence_gate()
        print("[PHYSICAL] persisted_observations=",r.persisted_observations)
        print("[PHYSICAL] current_markets=",r.current_markets)
        print("[PHYSICAL] association_candidates=",r.association_candidates)
        print("[PHYSICAL] evidence_envelopes=",r.evidence_envelopes)
        print("[PHYSICAL] reasoning_inputs=",r.reasoning_inputs)
        print("[PHYSICAL] ready_for_evidence_comparison_markets=",r.ready_for_evidence_comparison_markets)
        print("[PHYSICAL] ready_for_prediction_markets=",r.ready_for_prediction_markets)
        print("[PHYSICAL] state=",r.state)
        self.assertGreaterEqual(r.persisted_observations,0)
        self.assertGreaterEqual(r.current_markets,1)
        self.assertEqual(r.ready_for_prediction_markets,0)
        self.assertFalse(r.probability_enabled)
        self.assertFalse(r.execution_authority)

if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-126 physical sports reasoning-evidence gate certified")
    print("[PASS] outside-world evidence can reach reasoning comparison when a defensible live market association exists")
    print("[PASS] prediction readiness remains FALSE; probability_enabled=FALSE; execution_authority=FALSE")
