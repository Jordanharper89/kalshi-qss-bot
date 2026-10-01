import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_053_remaining_dex_parity_foundation as q

class T(unittest.TestCase):
    def test_mode(self):
        self.assertTrue(q.PAPER_ONLY)
        self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_freshness(self):
        self.assertEqual(q.MAX_AGE_MS,750.0)
    def test_three_remaining_venues(self):
        self.assertEqual(
            {"METEORA_DAMM_V2","RAYDIUM_CLMM","ORCA_WHIRLPOOL"},
            {"METEORA_DAMM_V2","RAYDIUM_CLMM","ORCA_WHIRLPOOL"}
        )

if __name__=="__main__": unittest.main(verbosity=2)
