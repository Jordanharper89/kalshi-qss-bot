\

import unittest
from qseries_v2.oracle_adapters.independent.oad_267_solana_pool_liquidity_historical_state import SolanaHistoricalObservation
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import *
def row(i,t,p):
    return SolanaHistoricalObservation(i,"S","solana_token_pool_identity_liquidity",t,None,"dex","X",
      {"token_address":"X","pools":({"pair_address":"P","liquidity_usd":100+p*10,"buys_h24":10+p,"sells_h24":8,"volume_h24":100+p*10,"price_usd":p},)})
class T(unittest.TestCase):
    def test_cases(self):
        x=build_outcome_pending_solana_cases((row("a","2026-09-01T00:00:00+00:00",1.0),row("b","2026-09-01T00:00:05+00:00",1.1)))
        print("[CASES]",len(x),tuple(c.horizon_seconds for c in x))
        self.assertEqual(tuple(c.horizon_seconds for c in x),(15,30,60))
        self.assertTrue(all(c.state=="OUTCOME_PENDING" for c in x))
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-313 Solana temporal cases formed without fabricating outcomes")

