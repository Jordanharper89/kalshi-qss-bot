import inspect
import unittest
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.hotpath import HotBook, QuoteUpdate, benchmark

class T(unittest.TestCase):
    def test_fresh_positive(self):
        b=HotBook()
        now=perf_counter_ns()
        self.assertIsNone(b.ingest(QuoteUpdate("T","P","M","PUMPSWAP","PUMP_TO_METEORA",0.05,0.054,now,1)))
        s=b.ingest(QuoteUpdate("T","P","M","METEORA_DLMM","PUMP_TO_METEORA",0.05,0.054,now,2))
        self.assertIsNotNone(s)
        self.assertLessEqual(s.route_age_ms,750.0)
        print("[PASS] fresh profitable Pump->Meteora signal admitted")

    def test_stale_rejected(self):
        b=HotBook()
        old=perf_counter_ns()-800_000_000
        b.ingest(QuoteUpdate("T","P","M","PUMPSWAP","PUMP_TO_METEORA",0.05,0.054,old,1))
        s=b.ingest(QuoteUpdate("T","P","M","METEORA_DLMM","PUMP_TO_METEORA",0.05,0.054,perf_counter_ns(),2))
        self.assertIsNone(s)
        print("[PASS] >750ms route rejected")

    def test_reverse(self):
        b=HotBook()
        now=perf_counter_ns()
        b.ingest(QuoteUpdate("T","P","M","METEORA_DLMM","METEORA_TO_PUMP",0.05,0.054,now,1))
        s=b.ingest(QuoteUpdate("T","P","M","PUMPSWAP","METEORA_TO_PUMP",0.05,0.054,now,2))
        self.assertIsNotNone(s)
        print("[PASS] reverse Meteora->Pump supported")

    def test_no_io_in_ingest(self):
        src=inspect.getsource(HotBook.ingest).lower()
        for bad in ("rpc(","urllib","requests","open(","sleep(","subprocess","path("):
            self.assertNotIn(bad,src)
        print("[PASS] hot ingest has no network/filesystem/sleep")

    def test_benchmark(self):
        r=benchmark(5000)
        self.assertTrue(r["under_750ms"])
        self.assertLess(r["p99_us"],750000)
        print("[PASS] p99_us=%.2f"%r["p99_us"])

if __name__=="__main__":
    unittest.main(verbosity=2)
