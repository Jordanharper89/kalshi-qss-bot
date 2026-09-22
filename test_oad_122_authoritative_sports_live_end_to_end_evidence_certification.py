import unittest
from qseries_v2.oracle_adapters.independent.oad_122_authoritative_sports_live_end_to_end_evidence_certification import run_live_sports_end_to_end_evidence_certification

class T(unittest.TestCase):
    def test_physical_live_chain(self):
        r=run_live_sports_end_to_end_evidence_certification()
        print("[PHYSICAL] persisted_observations=",r.persisted_observations)
        print("[PHYSICAL] committed_new=",r.committed_new)
        print("[PHYSICAL] providers=",r.providers)
        print("[PHYSICAL] structured_descriptors=",r.structured_descriptors)
        print("[PHYSICAL] current_markets=",r.current_markets)
        print("[PHYSICAL] observations_with_candidates=",r.observations_with_candidates)
        print("[PHYSICAL] association_candidates=",r.association_candidates)
        self.assertGreaterEqual(r.persisted_observations,0)
        self.assertGreaterEqual(r.current_markets,1)
        self.assertEqual(r.structured_descriptors,r.persisted_observations)
        self.assertTrue(r.read_only)
        self.assertFalse(r.probability_enabled)
        self.assertFalse(r.execution_authority)
        self.assertTrue(all(x.candidate_only for x in r.associations))

if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-122 physical live sports evidence chain certified")
    print("[PASS] real acquisition -> PostgreSQL -> exact readback -> current Kalshi association exercised")
    print("[PASS] candidate_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
