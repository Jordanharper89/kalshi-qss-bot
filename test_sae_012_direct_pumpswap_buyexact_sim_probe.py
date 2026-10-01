from pathlib import Path
import unittest

class T(unittest.TestCase):

    def test_probe_exists(self):
        p=Path(
            "qseries_v2/oracle_strategy_intelligence/"
            "solana_money/qsb059d_pump_native/"
            "sae012_direct_pumpswap_buyexact_sim_probe.mjs"
        )
        self.assertTrue(p.is_file())

    def test_no_send_transaction(self):
        p=Path(
            "qseries_v2/oracle_strategy_intelligence/"
            "solana_money/qsb059d_pump_native/"
            "sae012_direct_pumpswap_buyexact_sim_probe.mjs"
        )
        s=p.read_text(encoding="utf-8")
        self.assertNotIn("sendTransaction(",s)
        self.assertIn("simulateTransaction",s)
        self.assertIn("buyExactQuoteIn",s)
        self.assertIn("sigVerify:false",s)

    def test_four_physical_pools(self):
        s=Path(
            "qseries_v2/oracle_strategy_intelligence/"
            "solana_money/qsb059d_pump_native/"
            "sae012_direct_pumpswap_buyexact_sim_probe.mjs"
        ).read_text(encoding="utf-8")

        self.assertEqual(
            s.count('"5mfeK1')+
            s.count('"5wNu5Q')+
            s.count('"4w2cys')+
            s.count('"B3QKPL'),
            4
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
