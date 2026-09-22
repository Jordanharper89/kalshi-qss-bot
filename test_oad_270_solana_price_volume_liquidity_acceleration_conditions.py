import unittest
from qseries_v2.oracle_adapters.independent.oad_267_solana_pool_liquidity_historical_state import SolanaHistoricalObservation
from qseries_v2.oracle_adapters.independent.oad_270_solana_price_volume_liquidity_acceleration_conditions import *

class T(unittest.TestCase):
    def test_conditions(self):
        a=SolanaHistoricalObservation("a","S","solana_token_pool_identity_liquidity","t1",1,"dex","X",{"token_address":"X","pools":({"pair_address":"P","liquidity_usd":100,"buys_h24":10,"sells_h24":9,"volume_h24":100,"price_usd":1.0},)})
        b=SolanaHistoricalObservation("b","S","solana_token_pool_identity_liquidity","t2",2,"dex","X",{"token_address":"X","pools":({"pair_address":"P","liquidity_usd":125,"buys_h24":15,"sells_h24":10,"volume_h24":130,"price_usd":1.1},)})
        r=build_solana_acceleration_conditions((a,b))[0]
        print("[CONDITIONS]",r.conditions)
        print("[STATE]",r.state)
        self.assertEqual(r.state,"COMPOSITE_READY")
        self.assertIsNone(r.probability)
        self.assertIsNone(r.direction)

if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-270 factual acceleration-condition formation certified")
    print("[PASS] no probability or direction inferred")
