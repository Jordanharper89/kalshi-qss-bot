import unittest
from qseries_v2.oracle_adapters.independent.oad_304_solana_creator_deployer_claim_intelligence import *
class T(unittest.TestCase):
    def test_physical(self):
        r=acquire_current_creator_deployer_claims()
        print("[PHYSICAL] token=",r.token_address); print("[PHYSICAL] creator_deployer_claims=",r.claim_count)
        for x in r.claims[:3]: print("[CLAIM]",x.field_path,x.value[:80],"oracle_verified=",x.oracle_verified)
        self.assertEqual(r.claim_count,len(r.claims)); self.assertTrue(r.provider_claim_only)
        self.assertTrue(all(x.provider=="gmgn" and x.oracle_verified is False for x in r.claims))
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-304 creator/deployer extraction physically certified without promoting provider claims to truth")
