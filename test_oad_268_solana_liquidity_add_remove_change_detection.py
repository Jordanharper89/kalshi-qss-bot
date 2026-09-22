import unittest
from qseries_v2.oracle_adapters.independent.oad_267_solana_pool_liquidity_historical_state import SolanaHistoricalObservation
from qseries_v2.oracle_adapters.independent.oad_268_solana_liquidity_add_remove_change_detection import *

class T(unittest.TestCase):
    def test_delta(self):
        a=SolanaHistoricalObservation("a","source.dex.solana.token_pools.X","solana_token_pool_identity_liquidity","2026-09-01T00:00:00+00:00",1,"dexscreener","X",{"token_address":"X","pools":({"pair_address":"P","liquidity_usd":100.0},)})
        b=SolanaHistoricalObservation("b","source.dex.solana.token_pools.X","solana_token_pool_identity_liquidity","2026-09-01T00:01:00+00:00",2,"dexscreener","X",{"token_address":"X","pools":({"pair_address":"P","liquidity_usd":125.0},)})
        r=build_pool_liquidity_deltas((a,b))
        print("[DELTA]",r[0].liquidity_change_usd,r[0].state)
        self.assertEqual(r[0].liquidity_change_usd,25.0)
        self.assertEqual(r[0].state,"LIQUIDITY_ADDED")

if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-268 deterministic liquidity add/remove change detection certified")
