
import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_018c_live_stdout_money_handoff import (
    parse_fast_entries, parse_fresh_money, qualifies_existing_qsb015_entry,
    EXECUTION_AUTHORITY, PAPER_ONLY
)

class T(unittest.TestCase):
    def test_exact_user_log_fast_entry(self):
        line='[FAST ENTRIES] [{"family": "ORCA", "token": "BABANGA4JE7Kkam4nTrALAwAVgsNJUuFJnnkF7S16BZp", "score": 0.95, "liq": 229406.1}]'
        rows=parse_fast_entries(line)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0].family,"ORCA")
        self.assertEqual(rows[0].token,"BABANGA4JE7Kkam4nTrALAwAVgsNJUuFJnnkF7S16BZp")
        self.assertAlmostEqual(rows[0].score,0.95)
        self.assertAlmostEqual(rows[0].liquidity_usd,229406.1)
        self.assertTrue(qualifies_existing_qsb015_entry(rows[0]))

    def test_fresh_money(self):
        x=parse_fresh_money("[FRESH MONEY] closed=9 wins=6 losses=3 win_rate=0.6667 NET=$5.0086")
        self.assertEqual(x["closed"],9)
        self.assertEqual(x["wins"],6)
        self.assertAlmostEqual(x["net"],5.0086)

    def test_authority(self):
        self.assertFalse(EXECUTION_AUTHORITY)
        self.assertTrue(PAPER_ONLY)

if __name__=="__main__":
    unittest.main(verbosity=2)
