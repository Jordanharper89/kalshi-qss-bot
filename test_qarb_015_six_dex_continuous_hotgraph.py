
import inspect,unittest
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.multidex_live_hunter import *
class T(unittest.TestCase):
    def test_six_dex_matrix(self):
        m=capability_matrix();self.assertEqual(set(m),set(VENUES))
        self.assertTrue(m["RAYDIUM_CPMM"]["local_quote"])
        self.assertTrue(m["METEORA_DAMM_V2"]["local_quote"])
        self.assertTrue(m["RAYDIUM_CLMM"]["local_quote_provider_required"])
        self.assertTrue(m["ORCA_WHIRLPOOL"]["local_quote_provider_required"])
        print("[PASS] six-DEX capability truth matrix")
    def test_event_reprices_graph(self):
        h=HotGraph();now=perf_counter_ns()
        self.assertIsNone(h.publish(VenueQuote("RAYDIUM_CPMM","T","WSOL","T",50,100,now,"A")))
        r=h.publish(VenueQuote("METEORA_DAMM_V2","T","T","WSOL",100,55,now,"B"))
        self.assertIsNotNone(r);self.assertEqual(r["net"],5)
        print("[PASS] each fresh event can reprice cross-venue graph")
    def test_stale_fail_closed(self):
        h=HotGraph();old=perf_counter_ns()-800_000_000
        h.publish(VenueQuote("RAYDIUM_CPMM","T","WSOL","T",50,100,old,"A"))
        self.assertIsNone(h.publish(VenueQuote("METEORA_DAMM_V2","T","T","WSOL",100,55,old,"B")))
        print("[PASS] >750ms graph state cannot signal")
    def test_no_hot_io(self):
        src=inspect.getsource(HotGraph.publish).lower()
        for bad in ("rpc(","requests","urllib","open(","sleep(","subprocess"):
            self.assertNotIn(bad,src)
        print("[PASS] six-DEX graph publish has no network/filesystem/sleep")
if __name__=="__main__": unittest.main(verbosity=2)
