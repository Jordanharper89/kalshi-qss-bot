
import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_017_early_buyer_wallet_quality_gate import evaluate, EXECUTION_AUTHORITY, PAPER_ONLY

class T(unittest.TestCase):
    def test_early_buyer_can_admit_before_mature_volume(self):
        flow=[
            {"wallet":"A","side":"BUY","age_seconds":1.2},
            {"wallet":"B","side":"BUY","age_seconds":2.0},
            {"wallet":"C","side":"BUY","age_seconds":3.1},
            {"wallet":"D","side":"SELL","age_seconds":4.0},
        ]
        claims=[
            {"wallet":"A","win_rate":0.68,"closed_trades":44,"realized_pnl":920},
            {"wallet":"B","win_rate":61,"closed_trades":31,"realized_pnl":410},
            {"wallet":"C","win_rate":0.40,"closed_trades":50,"realized_pnl":-20},
        ]
        r=evaluate("MINT",flow,claims,liquidity_usd=1800)
        self.assertTrue(r.admitted)
        self.assertEqual(r.qualified_wallets,2)
        self.assertEqual(r.reason,"EARLY_BUYER_EDGE_PAPER_ADMISSION")
        self.assertFalse(EXECUTION_AUTHORITY)
        self.assertTrue(PAPER_ONLY)

    def test_fail_closed_without_executable_liquidity(self):
        flow=[{"wallet":"A","side":"BUY","age_seconds":1},{"wallet":"B","side":"BUY","age_seconds":2}]
        claims=[
            {"wallet":"A","win_rate":0.7,"closed_trades":20,"realized_pnl":10},
            {"wallet":"B","win_rate":0.7,"closed_trades":20,"realized_pnl":10},
        ]
        r=evaluate("M",flow,claims,liquidity_usd=200)
        self.assertFalse(r.admitted)
        self.assertEqual(r.reason,"MIN_EXECUTABLE_LIQUIDITY_FAIL")

if __name__=="__main__":
    unittest.main(verbosity=2)
