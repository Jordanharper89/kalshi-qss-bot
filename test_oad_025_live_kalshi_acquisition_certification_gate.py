import unittest
from qseries_v2.oracle_adapters.kalshi.oad_025_live_acquisition_gate import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_oad_025_live_kalshi_acquisition_certification_gate())

    def test_historical_nonblocking(self):
        self.assertFalse(
            build_oad_025_certification_manifest()["historical_reconciliation_blocks_live_startup"]
        )

    def test_live_ticker_selection(self):
        markets=(
            {"ticker":"A","status":"settled"},
            {"ticker":"B","status":"open"},
            {"ticker":"C","status":"open"},
        )
        self.assertEqual(select_live_probe_tickers(markets,5),("B","C"))

    def test_next(self):
        self.assertIn(
            "oracle_live_runtime",
            build_oad_025_certification_manifest()["next_capability"],
        )

if __name__=="__main__":
    print("="*72)
    print(" OAD-025 CORRECTION V2 CERTIFICATION TEST")
    print(" LIVE-FIRST KALSHI ACQUISITION GATE")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-025 live-first nonblocking acquisition gate certified")
    print("[DONE] OAD-025 CORRECTION V2 CERTIFIED")
