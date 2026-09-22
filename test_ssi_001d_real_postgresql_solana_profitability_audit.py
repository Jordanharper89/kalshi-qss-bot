
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_001_real_postgresql_solana_profitability_audit import audit
class T(unittest.TestCase):
    def test_physical(self):
        r=audit()
        print("[PHYSICAL]",r)
        self.assertTrue(r["physical_postgresql"])
        self.assertGreater(r["solana_rows"],0)
        self.assertGreater(r["economic_events"]+r["finalized_transactions"],0)
        self.assertFalse(r["execution_authority"])
        print("[GATE] exact_price_path_input_ready=",r["exact_price_path_input_ready"])
if __name__=="__main__":
    unittest.main(verbosity=2)
