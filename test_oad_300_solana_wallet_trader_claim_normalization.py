import unittest
from qseries_v2.oracle_adapters.independent.oad_300_solana_wallet_trader_claim_normalization import *
class T(unittest.TestCase):
    def test_physical(self):
        r=normalize_current_gmgn_wallet_trader_intelligence()
        print("[PHYSICAL] token=",r.token_address); print("[PHYSICAL] holder_rows=",r.holder_rows); print("[PHYSICAL] trader_rows=",r.trader_rows); print("[PHYSICAL] provider_claims=",len(r.provider_claims))
        self.assertTrue(r.token_address); self.assertEqual(len(r.provider_claims),r.holder_rows+r.trader_rows)
        self.assertTrue(all(x.provider=="gmgn" and x.oracle_verified is False for x in r.provider_claims))
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-300 wallet/trader provider-claim normalization physically certified")
    print("[PASS] GMGN labels remain provider claims, not Oracle truth")
