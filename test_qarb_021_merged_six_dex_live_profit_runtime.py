import unittest
from time import perf_counter_ns
import qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.merged_live_runtime as m
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.merged_live_runtime import Endpoint,evaluate_token

class T(unittest.TestCase):
    def test_crossvenue_profit(self):
        old=m.SIZES;m.SIZES=(0.00000005,)
        try:
            a=Endpoint("A","T","P1",lambda x:100,lambda x:45)
            b=Endpoint("B","T","P2",lambda x:90,lambda x:55)
            r=evaluate_token("T",[a,b],0,perf_counter_ns())
        finally:m.SIZES=old
        self.assertIsNotNone(r);self.assertEqual(r["buy_venue"],"A");self.assertEqual(r["sell_venue"],"B");self.assertTrue(r["qualified"])
        print("[PASS] fresh event -> positive cross-venue route")

    def test_stale_rejected(self):
        a=Endpoint("A","T","P1",lambda x:100,lambda x:45)
        b=Endpoint("B","T","P2",lambda x:90,lambda x:55)
        self.assertIsNone(evaluate_token("T",[a,b],0,perf_counter_ns()-800_000_000))
        print("[PASS] >750ms event rejected")

    def test_same_venue_rejected(self):
        old=m.SIZES;m.SIZES=(0.00000005,)
        try:
            a=Endpoint("A","T","P1",lambda x:100,lambda x:1000)
            r=evaluate_token("T",[a],0,perf_counter_ns())
        finally:m.SIZES=old
        self.assertIsNone(r)
        print("[PASS] same venue cannot self-arbitrage")

if __name__=="__main__": unittest.main(verbosity=2)
