
import unittest
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex.orca_whirlpool_live import *
class T(unittest.TestCase):
    def test_fail_closed(self):
        d=LivePool("P","A","B",("X",))
        with self.assertRaisesRegex(RuntimeError,"NOT_BOUND"): quote(d,"A",1)
        print("[PASS] Orca refuses fake pricing without native local provider")
    def test_provider_binding(self):
        d=LivePool("P","A","B",("X",))
        bind(d,provider=lambda desc,mint,x:x+5)
        self.assertTrue(touch(d,"X",b"x",perf_counter_ns()))
        self.assertEqual(quote(d,"B",8),13)
        print("[PASS] Orca live account touch -> bound local quote provider")
if __name__=="__main__": unittest.main(verbosity=2)
