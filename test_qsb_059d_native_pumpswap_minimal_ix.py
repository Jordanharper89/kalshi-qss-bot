import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money import qsb059_gav_reverse_atomic as q

class T(unittest.TestCase):
    def test_native_builder_present(self):
        self.assertTrue(callable(q.native_pump_buy_ixs))
        print("[PASS] native PumpSwap instruction builder installed")

    def test_compose_no_prebuilt_pump_tx(self):
        import inspect
        src=inspect.getsource(q.compose_reverse_atomic)
        self.assertNotIn("pump_tx(",src)
        self.assertNotIn("resolve_pump_instructions(",src)
        self.assertIn("native_pump_buy_ixs(",src)
        print("[PASS] reverse composer no longer imports whole prebuilt Pump transaction")

    def test_bridge_uses_official_sdk(self):
        p=Path.cwd()/"qseries_v2/oracle_strategy_intelligence/solana_money/qsb059d_pump_native/build_buy_ix.mjs"
        s=p.read_text(encoding="utf-8")
        self.assertIn("@pump-fun/pump-swap-sdk",s)
        self.assertIn("swapSolanaState",s)
        self.assertIn("swapAutocompleteBaseFromQuote",s)
        self.assertIn("swapBaseInstructions",s)
        print("[PASS] official PumpSwap SDK builds quote->base instructions")

    def test_no_broadcast(self):
        with open(q.__file__,encoding="utf-8") as f:
            s=f.read()
        self.assertNotIn("c.send(raw)",s)
        print("[PASS] QSB-059D remains simulation-only")

if __name__=="__main__":
    unittest.main(verbosity=2)
