import unittest
from qseries_v2.oracle_adapters.independent.oad_267_solana_pool_liquidity_historical_state import SolanaHistoricalObservation
from qseries_v2.oracle_adapters.independent.oad_269_solana_buy_sell_volume_pressure_history import *

class T(unittest.TestCase):
    def test_pressure(self):
        a=SolanaHistoricalObservation("a","S","solana_token_pool_identity_liquidity","t1",1,"dex","X",{"pools":({"pair_address":"P","buys_h24":10,"sells_h24":9,"volume_h24":100,"price_usd":1.0},)})
        b=SolanaHistoricalObservation("b","S","solana_token_pool_identity_liquidity","t2",2,"dex","X",{"pools":({"pair_address":"P","buys_h24":15,"sells_h24":10,"volume_h24":130,"price_usd":1.1},)})
        r=build_pool_pressure_history((a,b))[0]
        print("[PRESSURE]",r.buy_sell_imbalance,r.volume_change,r.price_change_fraction,r.state)
        self.assertEqual(r.buy_sell_imbalance,5)
        self.assertEqual(r.volume_change,30.0)
        self.assertEqual(r.state,"BUY_PRESSURE")

if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-269 buy/sell + volume-pressure history certified")
