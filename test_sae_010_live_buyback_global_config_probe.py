from pathlib import Path
import unittest

class T(unittest.TestCase):

    def test_probe_installed(self):
        p=Path(
            "qseries_v2/oracle_strategy_intelligence/"
            "solana_money/qsb059d_pump_native/"
            "sae010_live_buyback_global_config_probe.mjs"
        )
        self.assertTrue(p.is_file())
        s=p.read_text(encoding="utf-8")
        self.assertIn("GLOBAL_CONFIG_PDA",s)
        self.assertIn("SAE010_BUYBACK",s)
        self.assertIn("EXPECTED_8_BUYBACK_RECIPIENTS",s)

if __name__=="__main__":
    unittest.main(verbosity=2)
