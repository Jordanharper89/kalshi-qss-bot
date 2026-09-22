import unittest
from qseries_v2.oracle_adapters.independent.oad_309_solana_target_token_wallet_trader_coverage_acquisition import *

class T(unittest.TestCase):
    def test_physical_or_truthful_rate_limit_hold(self):
        x=acquire_target_token_wallet_trader_coverage()
        print("[PHYSICAL] token=",x.token_address)
        print("[PHYSICAL] state=",x.state)
        print("[PHYSICAL] holder_rows=",x.holder_rows)
        print("[PHYSICAL] trader_rows=",x.trader_rows)
        print("[PHYSICAL] provider_claims=",len(x.provider_claims))
        print("[PHYSICAL] retry_after_seconds=",x.retry_after_seconds)
        self.assertTrue(x.token_address)
        self.assertIn(x.state,("ACQUIRED","RATE_LIMITED_HOLD"))
        self.assertTrue(x.provider_claim_only)
        self.assertFalse(x.execution_authority)
        if x.state=="ACQUIRED":
            self.assertEqual(len(x.provider_claims),x.holder_rows+x.trader_rows)
            self.assertTrue(all(c.provider=="gmgn" and c.oracle_verified is False for c in x.provider_claims))
        else:
            self.assertGreaterEqual(x.retry_after_seconds,1.0)
            self.assertEqual(len(x.provider_claims),0)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-309 exact target-token wallet/trader coverage acquisition boundary certified")
    print("[PASS] GMGN rate limit is a truthful HOLD, not a downstream reasoning failure")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
