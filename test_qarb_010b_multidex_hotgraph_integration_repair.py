
import inspect,unittest
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.multidex_graph import *

class T(unittest.TestCase):
    def test_all_venues(self):
        self.assertEqual(set(VENUES),{
            "PUMPSWAP","METEORA_DLMM","RAYDIUM_CPMM",
            "RAYDIUM_CLMM","ORCA_WHIRLPOOL","METEORA_DAMM_V2"
        })
        self.assertEqual(len(route_pairs()),30)
        print("[PASS] six DEX families produce 30 directed two-leg venue routes")

    def test_crossvenue_profit(self):
        now=perf_counter_ns()
        qs=[
            VenueQuote("RAYDIUM_CPMM","T","SOL","T",50,100,now,"A"),
            VenueQuote("ORCA_WHIRLPOOL","T","T","SOL",100,55,now,"B"),
        ]
        r=best_two_leg(qs,"SOL","SOL",now)
        self.assertEqual(r["net"],5)
        self.assertEqual(r["buy_venue"],"RAYDIUM_CPMM")
        print("[PASS] local multi-DEX graph chooses positive cross-venue route")

    def test_stale_not_routed(self):
        old=perf_counter_ns()-800_000_000
        qs=[
            VenueQuote("RAYDIUM_CPMM","T","SOL","T",50,100,old,"A"),
            VenueQuote("ORCA_WHIRLPOOL","T","T","SOL",100,55,old,"B"),
        ]
        self.assertIsNone(best_two_leg(qs,"SOL","SOL",perf_counter_ns()))
        print("[PASS] multi-DEX graph rejects >750ms route state")

    def test_no_hot_io(self):
        src=inspect.getsource(best_two_leg).lower()
        for bad in ("rpc(","requests","urllib","open(","sleep(","subprocess"):
            self.assertNotIn(bad,src)
        print("[PASS] multi-DEX route graph has no hot-path I/O")

if __name__=="__main__":
    unittest.main(verbosity=2)
