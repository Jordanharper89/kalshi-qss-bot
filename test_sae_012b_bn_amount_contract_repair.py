from pathlib import Path
import unittest

P=Path(
    "qseries_v2/oracle_strategy_intelligence/"
    "solana_money/qsb059d_pump_native/"
    "sae012_direct_pumpswap_buyexact_sim_probe.mjs"
)

class T(unittest.TestCase):
    def test_bn_contract(self):
        s=P.read_text(encoding="utf-8")
        self.assertIn('import BN from "bn.js";',s)
        self.assertIn('new BN("1")',s)
        self.assertIn('new BN("1000000")',s)

    def test_simulation_only(self):
        s=P.read_text(encoding="utf-8")
        self.assertIn("simulateTransaction",s)
        self.assertNotIn("sendTransaction(",s)

if __name__=="__main__":
    unittest.main(verbosity=2)
