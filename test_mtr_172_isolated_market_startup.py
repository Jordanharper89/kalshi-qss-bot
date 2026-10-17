
import unittest
from unittest.mock import patch
from qseries_v2.oracle_execution.solana_atomic_executor import (
    mtr_172_isolated_market_startup as m
)

class Tests(unittest.TestCase):
    def test_key_stripped(self):
        result = m.clean_environment({
            "QSB_SOLANA_PRIVATE_KEY": "secret",
            "SAFE": "value",
        })
        self.assertNotIn("QSB_SOLANA_PRIVATE_KEY", result)
        self.assertEqual(result["SAFE"], "value")

    def test_other_secret_names(self):
        result = m.clean_environment({
            "WALLET_PRIVATE_KEY": "secret",
            "MY_SEED_PHRASE": "secret",
        })
        self.assertEqual(result, {})

    def test_runtime_transport(self):
        rt = m.verify_transport()
        self.assertTrue(callable(rt.serve_canonical))

    def test_async_transport(self):
        import asyncio
        rt = m.verify_transport()
        self.assertTrue(
            asyncio.iscoroutinefunction(rt.serve_canonical)
        )

    def test_live_mode_disabled(self):
        with patch("sys.argv", ["mtr172", "--live"]):
            with self.assertRaises(m.StartupHold):
                m.main()

if __name__ == "__main__":
    unittest.main(verbosity=2)
