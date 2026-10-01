
import unittest
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex.raydium_clmm_live import *
class T(unittest.TestCase):
    def test_fail_closed_without_provider(self):
        d=LivePool("P","A","B",("X",))
        with self.assertRaisesRegex(RuntimeError,"NOT_BOUND"): quote(d,"A",1)
        print("[PASS] Raydium CLMM refuses fake pricing when no native local provider bound")
    def test_provider_binding_and_touch(self):
        d=LivePool("P","A","B",("X","Y"))
        bind(d,provider=lambda desc,mint,x:x*3)
        self.assertTrue(touch(d,"X",b"abc",perf_counter_ns()))
        self.assertEqual(quote(d,"A",7),21)
        print("[PASS] Raydium CLMM live account touch -> bound local quote provider")
if __name__=="__main__": unittest.main(verbosity=2)
