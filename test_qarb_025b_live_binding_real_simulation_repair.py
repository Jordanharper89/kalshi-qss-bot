import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_025b_live_binding_real_simulation_repair as q

class T(unittest.TestCase):
    def test_meta_dict_pool(self):
        r={"token":"T","pump_pool":"P","meteora_meta":{"pool":"M"}}
        self.assertEqual(q.meteora_pool_from_row(r),"M")
        print("[PASS] current Meteora binding extracted from live universe row")

    def test_direct_pool(self):
        r={"token":"T","pump_pool":"P","meteora_pool":"M"}
        self.assertEqual(q.meteora_pool_from_row(r),"M")
        print("[PASS] direct current Meteora pool binding accepted")

    def test_execution_false(self):
        self.assertIs(q.execution_authority,False)
        print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    unittest.main(verbosity=2)
