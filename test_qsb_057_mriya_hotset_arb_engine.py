import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

class T(unittest.TestCase):
    def test_hot_tx_mints(self):
        tx={"meta":{"preTokenBalances":[{"mint":"TokenAAA"},{"mint":c.WSOL}],
                    "postTokenBalances":[{"mint":"TokenAAA"},{"mint":"TokenBBB"}]}}
        self.assertEqual(c._hot_token_mints_from_tx(tx),["TokenAAA","TokenBBB"])
        print("[PASS] recent target-wallet transactions yield dynamic token mints")

    def test_hot_first_merge(self):
        old_hot,old_tape,old_pool=c.mriya_hot_tokens,c.tape_candidates,c.canonical_pump_pool
        c.mriya_hot_tokens=lambda:[{"mint":"HOT","score":1,"age":2.0,"signature":"S"}]
        c.tape_candidates=lambda root:[("COLD","P2")]
        c.canonical_pump_pool=lambda token:"P1" if token=="HOT" else None
        try:
            x=c.mriya_first_candidates(".")
            self.assertEqual(x[0],("HOT","P1"))
            self.assertEqual(x[1],("COLD","P2"))
        finally:
            c.mriya_hot_tokens,c.tape_candidates,c.canonical_pump_pool=old_hot,old_tape,old_pool
        print("[PASS] hot wallet tokens are searched before fallback tape")

    def test_size_band(self):
        self.assertIn(0.15,c.SIZES_SOL)
        self.assertIn(0.6,c.SIZES_SOL)
        self.assertIn(1.25,c.SIZES_SOL)
        print("[PASS] size grid covers sub-SOL and >1-SOL bands")

    def test_no_jupiter(self):
        with open(c.__file__,encoding="utf-8") as f:
            src=f.read().lower()
        self.assertNotIn("jup.ag",src)
        self.assertNotIn("swap-instructions",src)
        print("[PASS] zero Jupiter hot-path code")

if __name__=="__main__":
    unittest.main(verbosity=2)
