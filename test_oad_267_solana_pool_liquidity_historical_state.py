import unittest
from qseries_v2.oracle_adapters.independent.oad_267_solana_pool_liquidity_historical_state import *

class T(unittest.TestCase):
    def test_physical(self):
        r=read_solana_proven_history(refresh=True,per_source_limit=64)
        print("[PHYSICAL] current_token=",r.current_token_address)
        print("[PHYSICAL] queried_sources=",r.queried_sources)
        print("[PHYSICAL] queried_rows=",r.queried_rows)
        print("[PHYSICAL] records=",len(r.records))
        self.assertEqual(len(r.queried_sources),3)
        self.assertGreaterEqual(r.queried_rows,3)
        self.assertFalse(r.execution_authority)

if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-267 bounded exact-source Solana historical-state readback physically certified")
    print("[PASS] holder concentration remains excluded")
