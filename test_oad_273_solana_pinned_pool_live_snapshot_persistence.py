import unittest
from qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence import *

class T(unittest.TestCase):
    def test_physical(self):
        token=select_live_solana_token()
        r=persist_pinned_solana_pool_snapshot(token)
        print("[PHYSICAL] token_address=",r.token_address)
        print("[PHYSICAL] source_id=",r.source_id)
        print("[PHYSICAL] provider=",r.provider)
        print("[PHYSICAL] pools=",r.pools)
        print("[PHYSICAL] committed_new=",r.committed_new)
        print("[PHYSICAL] exact_readback=",r.exact_readback)
        self.assertEqual(r.token_address,token)
        self.assertEqual(r.provider,"dexscreener")
        self.assertEqual(r.exact_readback,1)
        self.assertGreaterEqual(r.pools,1)
        self.assertFalse(r.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-273 live pinned Solana pool snapshot persisted through OPH-019")
    print("[PASS] exact PostgreSQL readback certified")
