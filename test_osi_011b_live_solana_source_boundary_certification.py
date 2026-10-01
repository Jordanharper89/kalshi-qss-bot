import json
import tempfile
import unittest
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_011_live_solana_source_boundary_certification import certify, write_report

ROOT = Path(__file__).resolve().parent

class TestOSI011B(unittest.TestCase):
    def test_spool_false_positive_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / "runtime" / "predictive_data"
            p.mkdir(parents=True)
            (p / "opd_061_live_anchor_spool.jsonl").write_text(
                '{"prediction_id":"x","anchor":1}\\n',
                encoding="utf-8",
            )
            result = certify(root, 900)
            self.assertFalse(result["live_boundary_certified"])
            self.assertEqual(result["live_source_count"], 0)

    def test_real_solana_shape_is_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / "runtime_state" / "solana"
            p.mkdir(parents=True)
            (p / "live_swap_events.jsonl").write_text(
                '{"mint":"M","timestamp":"2026-09-18T05:00:00+00:00","event_type":"swap"}\\n',
                encoding="utf-8",
            )
            result = certify(root, 900)
            self.assertTrue(result["live_boundary_certified"])
            self.assertEqual(result["live_source_count"], 1)

    def test_physical(self):
        result = certify(ROOT, 900)
        report = write_report(ROOT)
        print("[REPORT]", report)
        print("[LIVE_SOURCE_COUNT]", result["live_source_count"])
        print("[REJECTED_COUNT]", result["rejected_count"])
        if not result["live_boundary_certified"]:
            self.fail("NO_VERIFIED_PHYSICAL_SOLANA_RUNTIME_SOURCE")
        print("[PASS] OSI-011B verified live Solana source boundary")
        print("[TRADER] Oracle is now pointed at files that actually contain Solana-shaped market data")
        print("[PASS] execution_authority=FALSE")
        print("[SCOPE] Source certification only; downstream live intake must be re-certified")

if __name__ == "__main__":
    unittest.main()
