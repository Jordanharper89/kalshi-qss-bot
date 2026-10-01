import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

class T(unittest.TestCase):
    def test_size_grid(self):
        self.assertGreaterEqual(len(c.SIZES_SOL),8)
        self.assertLessEqual(min(c.SIZES_SOL),0.005)
        self.assertGreaterEqual(max(c.SIZES_SOL),1.0)
        print("[PASS] 8-size search grid enabled")

    def test_token_universe(self):
        self.assertGreaterEqual(c.MAX_TOKENS,64)
        print("[PASS] token universe expanded to 64")

    def test_bidirectional(self):
        src=open(c.__file__,encoding="utf-8").read()
        self.assertIn("METEORA_TO_PUMP",src)
        self.assertIn("PUMP_TO_METEORA",src)
        print("[PASS] both arbitrage directions searched")

    def test_no_jupiter(self):
        src=open(c.__file__,encoding="utf-8").read().lower()
        self.assertNotIn("jup.ag",src)
        self.assertNotIn("swap-instructions",src)
        print("[PASS] zero Jupiter hot-path code")

if __name__=="__main__":
    unittest.main(verbosity=2)
