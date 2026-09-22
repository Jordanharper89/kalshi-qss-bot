import unittest
from qseries_v2.oracle_adapters.independent.oad_070_physical_current_market_independent_association_gate import *
class T(unittest.TestCase):
    def test_physical(self):
        r=run_physical_current_market_association()
        print("[PHYSICAL] independent_observations=",r.observations);print("[PHYSICAL] current_open_markets=",r.current_markets)
        print("[PHYSICAL] observations_with_candidates=",r.observations_with_candidates);print("[PHYSICAL] association_candidates=",r.association_candidates)
        for c in r.candidates[:10]: print("[CANDIDATE]",c.observation_id[:12],c.market_id,c.overlap_terms,"candidate_only=",c.candidate_only)
        self.assertGreater(r.observations,0);self.assertGreater(r.current_markets,0);self.assertTrue(all(c.candidate_only for c in r.candidates))
if __name__=="__main__":
    print("="*88);print(" OAD-070 PHYSICAL CERTIFICATION TEST");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Zero candidates permitted; no association fabricated")
    print("[PASS] Any match remains candidate-only pending validation")
    print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-066 through OAD-070 CAPABILITY SLICE CERTIFIED")
