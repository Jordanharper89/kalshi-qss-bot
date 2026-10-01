import asyncio,unittest
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.persistent_profit_runtime import _p99,_best_text

class T(unittest.TestCase):
    def test_p99(self):
        self.assertEqual(_p99([1,2,3]),3)
        print("[PASS] latency scoreboard p99")
    def test_best_text(self):
        x={"net_sol":.001,"net_bps":20.0,"buy_venue":"A","sell_venue":"B"}
        self.assertIn("+0.001000000_SOL",_best_text(x))
        print("[PASS] heartbeat surfaces live best PNL")
    def test_no_window_rediscovery_contract(self):
        import inspect
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
        src=inspect.getsource(p.serve)
        self.assertEqual(src.count("m.prepare(root)"),1)
        self.assertNotIn("while True:\n        state=m.prepare",src)
        print("[PASS] production state hydrates once; no recurring REST discovery loop")
if __name__=="__main__":unittest.main(verbosity=2)
