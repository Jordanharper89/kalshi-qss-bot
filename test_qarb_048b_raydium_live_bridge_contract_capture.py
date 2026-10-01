import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_048b_raydium_live_bridge_contract_capture as q

class T(unittest.TestCase):
    def test_targets(self):
        self.assertEqual(len(q.TARGETS),3)
        self.assertTrue(any("qarb_011" in x for x in q.TARGETS))
        self.assertTrue(any("merged_live_runtime" in x for x in q.TARGETS))

if __name__=="__main__":unittest.main(verbosity=2)
