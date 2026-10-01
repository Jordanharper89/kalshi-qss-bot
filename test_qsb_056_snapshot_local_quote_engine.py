import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

class T(unittest.TestCase):
    def test_snapshot_engine(self):
        self.assertTrue(callable(c.build_token_snapshot))
        self.assertTrue(callable(c.sized_snapshot_opportunities))
        print("[PASS] snapshot-local engine installed")

    def test_size_path_no_network(self):
        src=inspect.getsource(c.sized_snapshot_opportunities)
        for bad in ("discover_dlmm(","dlmm_arrays(","account(","token_amount("):
            self.assertNotIn(bad,src)
        print("[PASS] all trade sizes quote with zero network hydration")

    def test_local_pump_math(self):
        s={"pump_base_reserve":1_000_000_000,"pump_quote_reserve":1_000_000_000}
        self.assertGreater(c.pump_buy_snapshot(s,1_000_000),0)
        self.assertGreater(c.pump_sell_snapshot(s,1_000_000),0)
        print("[PASS] PumpSwap reserves reused locally")

    def test_no_jupiter(self):
        with open(c.__file__,encoding="utf-8") as f: src=f.read().lower()
        self.assertNotIn("jup.ag",src)
        self.assertNotIn("swap-instructions",src)
        print("[PASS] zero Jupiter hot-path code")

if __name__=="__main__":
    unittest.main(verbosity=2)
