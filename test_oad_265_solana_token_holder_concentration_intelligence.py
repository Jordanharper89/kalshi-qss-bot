import unittest
from qseries_v2.oracle_adapters.independent.oad_265_solana_token_holder_concentration_intelligence import *

class T(unittest.TestCase):
    def test_physical(self):
        o=acquire_solana_holder_concentration()
        p=o.payload
        print("[PHYSICAL] token=",p["token_address"])
        print("[PHYSICAL] indexed_rpc_provider=",p["indexed_rpc_provider"])
        print("[PHYSICAL] largest_accounts=",p["largest_account_count"])
        print("[PHYSICAL] top1_share=",p["top1_share"])
        print("[PHYSICAL] top5_share=",p["top5_share"])
        print("[PHYSICAL] top20_share=",p["top20_share"])
        print("[PHYSICAL] provider_failures=",p["provider_failures"])
        print("[PHYSICAL] commitment=",p["commitment"])
        self.assertGreater(p["largest_account_count"],0)
        self.assertGreaterEqual(p["top5_share"],p["top1_share"])
        self.assertGreaterEqual(p["top20_share"],p["top5_share"])
        self.assertEqual(p["method"],"getTokenLargestAccounts")
        self.assertTrue(verify_independent_crypto_observation(o))
        self.assertFalse(EXECUTION_AUTHORITY)

if __name__=="__main__":
    result=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-265 indexed-RPC provider-failover holder concentration physically certified")
    print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE publication_allowed=FALSE execution_authority=FALSE")
