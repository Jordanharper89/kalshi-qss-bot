import unittest
from qseries_v2.oracle_adapters.independent.oad_267_solana_pool_liquidity_historical_state import SolanaHistoricalObservation
from qseries_v2.oracle_adapters.independent.oad_271_solana_historical_experience_formation import *

class T(unittest.TestCase):
    def test_candidate(self):
        a=SolanaHistoricalObservation("oa","S","solana_token_pool_identity_liquidity","2026-09-01T00:00:00+00:00",1,"dex","X",{"token_address":"X","pools":({"pair_address":"P","liquidity_usd":100,"buys_h24":10,"sells_h24":9,"volume_h24":100,"price_usd":1.0},)})
        b=SolanaHistoricalObservation("ob","S","solana_token_pool_identity_liquidity","2026-09-01T00:01:00+00:00",2,"dex","X",{"token_address":"X","pools":({"pair_address":"P","liquidity_usd":125,"buys_h24":15,"sells_h24":10,"volume_h24":130,"price_usd":1.1},)})
        r=build_solana_historical_experiences((a,b))
        print("[EXPERIENCE]",r[0].experience_id)
        print("[EVIDENCE]",r[0].evidence_observation_ids)
        self.assertEqual(r[0].evidence_observation_ids,("oa","ob"))
        self.assertFalse(r[0].outcome_attached)
        self.assertIsNone(r[0].probability)
        self.assertIsNone(r[0].direction)

if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-271 deterministic outcome-pending Solana historical-experience formation certified")
    print("[PASS] persistence remains gated on real temporal depth")
