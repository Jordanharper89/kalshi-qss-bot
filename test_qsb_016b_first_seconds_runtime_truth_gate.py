import tempfile, unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_016b_first_seconds_runtime_truth_gate import analyze_lines, write_report

class TruthGateTest(unittest.TestCase):
    def test_positive_native_lane(self):
        lines = [
            '[BURST] family=RAYDIUM_CPMM raw=1234 hot_rows=4 signature=abc slot=1',
            '[ENTRY] strategy=FIRST_SECONDS_LAUNCH_IMPULSE family=RAYDIUM_CPMM native_price=0.0001',
            '[CLOSED] strategy=FIRST_SECONDS_LAUNCH_IMPULSE result=WIN net_pnl=0.42',
            '[ENTRY] strategy=FIRST_SECONDS_LAUNCH_IMPULSE family=METEORA_DAMM pool_state_price=0.0002',
            '[CLOSED] strategy=FIRST_SECONDS_LAUNCH_IMPULSE result=WIN net_pnl=0.77',
        ]
        r = analyze_lines(lines)
        self.assertEqual(r.hot_rows_max, 4)
        self.assertEqual(r.first_seconds_entries, 2)
        self.assertEqual(r.closed_trades, 2)
        self.assertEqual(r.wins, 2)
        self.assertAlmostEqual(r.net_pnl, 1.19, places=8)
        self.assertGreater(r.family_hits['RAYDIUM_CPMM'], 0)
        self.assertGreater(r.direct_native_price_markers, 0)
        self.assertEqual(r.next_boundary, 'CONTINUE_FRESH_FORWARD_SAMPLE_TO_25_CLOSES')
        self.assertFalse(r.execution_authority)
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(write_report(r, Path(d)).exists())

    def test_no_hot_rows_routes_native(self):
        r = analyze_lines(['[BURST] family=PUMP_FUN hot_rows=0 signature=x slot=2'])
        self.assertEqual(r.next_boundary, 'QSB_017_NATIVE_POOL_IDENTITY_AND_PRICE_PATH')

if __name__ == '__main__': unittest.main()
