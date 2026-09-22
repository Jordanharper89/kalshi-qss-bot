import unittest

from qseries_v2.oracle_adapters.independent.oad_402_solana_zero_cost_surveillance_physical_gate import (
    run_zero_cost_physical_gate,
)

class T(unittest.TestCase):
    def test_physical_zero_cost_surveillance(self):
        x = run_zero_cost_physical_gate(
            attempts=5,
            progress=lambda *a, **k: print("[LIVE]", *a),
        )

        print("[PHYSICAL]", x)

        self.assertEqual(
            x.hard_failures,
            0,
            "non-transient failure occurred during zero-cost surveillance gate",
        )
        self.assertTrue(
            x.checkpoint_advanced,
            "durable Solana checkpoint did not advance after bounded transient-RPC recovery attempts",
        )
        self.assertTrue(
            x.lag_not_worse,
            "checkpoint lag materially worsened during bounded zero-cost surveillance run",
        )
        self.assertEqual(
            x.state,
            "ZERO_COST_SURVEILLANCE_CERTIFIED",
        )

if __name__ == "__main__":
    rr = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not rr.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-402 physical zero-cost Solana surveillance certified")
    print("[PASS] public-RPC timeout / temporary network failures treated as recoverable")
    print("[PASS] durable checkpoint preserved across transient failure")
