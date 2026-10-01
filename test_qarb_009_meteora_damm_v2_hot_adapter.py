
import inspect,unittest
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex.meteora_damm_v2 import *
class T(unittest.TestCase):
    def test_bidirectional(self):
        s=PoolState("P","SOL","T",2_000_000_000,4_000_000_000,30,10000,perf_counter_ns())
        self.assertGreater(quote_exact_in(s,"SOL",10_000_000),0)
        self.assertGreater(quote_exact_in(s,"T",10_000_000),0)
        print("[PASS] Meteora DAMM V2 local constant-product quote both directions")
    def test_stale(self):
        s=PoolState("P","SOL","T",1,2,30,10000,perf_counter_ns()-800_000_000)
        with self.assertRaisesRegex(RuntimeError,"STALE"): quote_exact_in(s,"SOL",1)
        print("[PASS] Meteora DAMM V2 >750ms state rejected")
    def test_no_hot_io(self):
        src=(inspect.getsource(quote_exact_in)+inspect.getsource(update_reserve)).lower()
        for bad in ("rpc(","requests","urllib","open(","sleep(","subprocess"): self.assertNotIn(bad,src)
        print("[PASS] DAMM V2 hot quote/update has no network/filesystem/sleep")
if __name__=="__main__": unittest.main(verbosity=2)
