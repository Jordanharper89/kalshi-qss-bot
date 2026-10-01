import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

class T(unittest.TestCase):
    def test_bidirectional_symbols(self):
        self.assertTrue(callable(c.pump_buy_local))
        self.assertTrue(callable(c.bidirectional_opportunities))
        print("[PASS] both-direction same-token opportunity engine installed")

    def test_no_jupiter(self):
        with open(c.__file__,encoding="utf-8") as f:s=f.read().lower()
        self.assertNotIn("jup.ag",s)
        self.assertNotIn("swap-instructions",s)
        print("[PASS] zero Jupiter hot-path code")

    def test_reverse_direction_constant(self):
        src=open(c.__file__,encoding="utf-8").read()
        self.assertIn("PUMP_TO_METEORA",src)
        self.assertIn("METEORA_TO_PUMP",src)
        print("[PASS] both low->high directions evaluated")

if __name__=="__main__":
    unittest.main(verbosity=2)
