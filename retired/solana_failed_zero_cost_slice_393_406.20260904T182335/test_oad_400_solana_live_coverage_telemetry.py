import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent.oad_400_solana_live_coverage_telemetry import capture_live_coverage
class H:
    slot=110; source="HTTP_FINALIZED_FALLBACK"
class T(unittest.TestCase):
    def test_telemetry(self):
        with patch("qseries_v2.oracle_adapters.independent.oad_400_solana_live_coverage_telemetry.observe_live_head",return_value=H()), patch("qseries_v2.oracle_adapters.independent.oad_400_solana_live_coverage_telemetry.read_last_committed_slot",return_value=108):
            x=capture_live_coverage()
        print("[COVERAGE]",x)
        self.assertEqual(x.checkpoint_lag,2)
        self.assertEqual(x.state,"CAUGHT_UP")
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-400 live checkpoint-lag telemetry certified")