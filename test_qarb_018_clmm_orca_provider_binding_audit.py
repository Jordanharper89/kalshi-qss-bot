
import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.provider_binding_audit import *
class T(unittest.TestCase):
    def test_audit_truthfully_reports_absent(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td,"qseries_v2").mkdir()
            d,p=write(td)
            self.assertIsNone(d["RAYDIUM_CLMM"]);self.assertIsNone(d["ORCA_WHIRLPOOL"]);self.assertTrue(p.exists())
        print("[PASS] provider audit fails closed instead of inventing CLMM/Orca math")
if __name__=="__main__": unittest.main(verbosity=2)
