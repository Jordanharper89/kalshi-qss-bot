
import inspect,unittest
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex.orca_whirlpool import *
class T(unittest.TestCase):
    def test_local_quoter_bridge(self):
        s=bind_local_quoter("P","SOL","T",lambda mint,x:x+9)
        self.assertEqual(quote_exact_in(s,"T",11),20)
        print("[PASS] Orca Whirlpool repo-native local quoter bridge")
    def test_stale(self):
        s=bind_local_quoter("P","SOL","T",lambda m,x:x,perf_counter_ns()-800_000_000)
        with self.assertRaisesRegex(RuntimeError,"STALE"): quote_exact_in(s,"SOL",1)
        print("[PASS] Orca >750ms state rejected")
    def test_no_adapter_io(self):
        src=inspect.getsource(quote_exact_in).lower()
        for bad in ("rpc(","requests","urllib","open(","sleep(","subprocess"): self.assertNotIn(bad,src)
        print("[PASS] Orca adapter performs no network/filesystem/sleep")
if __name__=="__main__": unittest.main(verbosity=2)
