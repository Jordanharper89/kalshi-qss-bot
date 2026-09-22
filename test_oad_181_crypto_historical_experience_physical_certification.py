import unittest
from qseries_v2.oracle_adapters.independent.oad_181_crypto_historical_experience_physical_certification import run_crypto_historical_experience_physical_certification
class T(unittest.TestCase):
    def test_physical(self):
        r=run_crypto_historical_experience_physical_certification()
        print("[PHYSICAL] runtime_ready=",r.runtime_ready)
        print("[PHYSICAL] candidates=",r.candidates)
        print("[PHYSICAL] verified_candidates=",r.verified_candidates)
        print("[PHYSICAL] verified_lineages=",r.verified_lineages)
        print("[PHYSICAL] committed_new=",r.committed_new)
        print("[PHYSICAL] exact_readback=",r.exact_readback)
        print("[PHYSICAL] outcome_pending=",r.outcome_pending)
        print("[PHYSICAL] learning_event_ready=",r.learning_event_ready)
        print("[PHYSICAL] assets=",r.assets)
        print("[PHYSICAL] physical_ready=",r.physical_ready)
        self.assertTrue(r.physical_ready)
        self.assertEqual(r.assets,("BTC","ETH","SOL"))
        self.assertEqual(r.outcome_pending,r.candidates)
        self.assertEqual(r.learning_event_ready,0)
        self.assertFalse(r.probability_enabled)
        self.assertFalse(r.direction_enabled)
        self.assertFalse(r.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-181 historical crypto experience formation physically certified")
    print("[PASS] experience candidates persist now; OCL learning remains gated on real verified outcomes")
