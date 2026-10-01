
import unittest,time
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_019_buy_pressure_ten_win_forward_trial import (
    Position,qualifies,close_reason,realized_pnl,milestone,EXECUTION_AUTHORITY,PAPER_ONLY
)

class T(unittest.TestCase):
    def test_buy_pressure_ready(self):
        row={
            "token_mint":"MINT1","pool":"POOL1","price":1.0,"liquidity_usd":5000,
            "buy_count":18,"sell_count":4,"volume":2200,"prev_volume":1000
        }
        ok,reason,score=qualifies(row)
        self.assertTrue(ok)
        self.assertEqual(reason,"READY")
        self.assertGreater(score,0.60)

    def test_positive_close_after_friction(self):
        p=Position("P1","POOL1","MINT1","PUMP_SWAP",1.015,1.0,5/1.015,5.0,time.time()-20,1.015)
        reason=close_reason(p,1.40,time.time())
        self.assertEqual(reason,"TAKE_PROFIT")
        pnl,exit_px=realized_pnl(p,1.40,0.03)
        self.assertGreater(pnl,0)

    def test_milestone_requires_ten_wins_and_positive_net(self):
        self.assertFalse(milestone({"wins":9,"net_pnl_usdc":100}))
        self.assertFalse(milestone({"wins":10,"net_pnl_usdc":0}))
        self.assertTrue(milestone({"wins":10,"net_pnl_usdc":0.01}))
        self.assertFalse(EXECUTION_AUTHORITY)
        self.assertTrue(PAPER_ONLY)

if __name__=="__main__":
    unittest.main(verbosity=2)
