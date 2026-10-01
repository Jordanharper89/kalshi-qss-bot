
import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_018b_unified_first_seconds_champion_runtime import (
    evaluate, EXECUTION_AUTHORITY, PAPER_ONLY
)

class T(unittest.TestCase):
    def test_unified_positive_case(self):
        flow=[
            {"wallet":"A","side":"BUY","age_seconds":1.0},
            {"wallet":"B","side":"BUY","age_seconds":2.0},
            {"wallet":"C","side":"BUY","age_seconds":3.0},
            {"wallet":"D","side":"SELL","age_seconds":4.0},
        ]
        claims=[
            {"wallet":"A","win_rate":0.68,"closed_trades":40,"realized_pnl":500},
            {"wallet":"B","win_rate":61,"closed_trades":25,"realized_pnl":300},
            {"wallet":"C","win_rate":0.45,"closed_trades":30,"realized_pnl":-5},
        ]
        r=evaluate("MINT",flow,claims,buy_pressure_score=1.7,liquidity_usd=2500)
        self.assertTrue(r.admitted)
        self.assertEqual(r.qualified_wallets,2)
        self.assertEqual(r.reason,"UNIFIED_FIRST_SECONDS_PAPER_ADMISSION")
        self.assertFalse(EXECUTION_AUTHORITY)
        self.assertTrue(PAPER_ONLY)

    def test_buy_pressure_still_required(self):
        flow=[
            {"wallet":"A","side":"BUY","age_seconds":1.0},
            {"wallet":"B","side":"BUY","age_seconds":2.0},
        ]
        claims=[
            {"wallet":"A","win_rate":0.7,"closed_trades":20,"realized_pnl":100},
            {"wallet":"B","win_rate":0.7,"closed_trades":20,"realized_pnl":100},
        ]
        r=evaluate("MINT",flow,claims,buy_pressure_score=0.1,liquidity_usd=2500)
        self.assertFalse(r.admitted)
        self.assertEqual(r.reason,"BUY_PRESSURE_FAIL")

if __name__=="__main__":
    unittest.main(verbosity=2)
