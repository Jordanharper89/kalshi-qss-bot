
import asyncio,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.six_dex_live_stream import *
class T(unittest.TestCase):
    def test_empty_plan_is_safe(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            Path(td,"runtime_state").mkdir()
            r=asyncio.run(run(td,0.01,8))
            self.assertEqual(r["subscriptions"],0);self.assertEqual(r["notifications"],0)
        print("[PASS] six-DEX live runtime safely handles zero certified accounts")
if __name__=="__main__": unittest.main(verbosity=2)
