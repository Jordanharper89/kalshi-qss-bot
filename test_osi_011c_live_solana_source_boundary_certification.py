import json
import tempfile
import unittest
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_011_live_solana_source_boundary_certification import certify, write_report

ROOT = Path(__file__).resolve().parent

class TestOSI011C(unittest.TestCase):
    def test_spool_false_positive_rejected_by_content(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / "runtime" / "predictive_data"
            p.mkdir(parents=True)
            (p / "opd_061_live_anchor_spool.jsonl").write_text(
                json.dumps({"prediction_id":"x","anchor":1}) + "\n",
                encoding="utf-8",
            )
            result = certify(root)
            self.assertFalse(result["live_boundary_certified"])

    def test_real_solana_shape_accepted_by_content(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / "runtime_state" / "anything"
            p.mkdir(parents=True)
            (p / "records.jsonl").write_text(
                json.dumps({
                    "mint":"M",
                    "timestamp":"2026-09-18T05:00:00+00:00",
                    "event_type":"swap",
                    "signature":"abc",
                }) + "\n",
                encoding="utf-8",
            )
            result = certify(root)
            self.assertTrue(result["live_boundary_certified"])
            self.assertEqual(result["live_source_count"], 1)

    def test_physical(self):
        result = certify(ROOT)
        report = write_report(ROOT)
        print("[REPORT]", report)
        print("[LIVE_SOURCE_COUNT]", result["live_source_count"])
        print("[REJECTED_COUNT]", result["rejected_count"])
        if result["live_sources"]:
            print("[TOP_SOURCE]", json.dumps(result["live_sources"][0], sort_keys=True))
        if not result["live_boundary_certified"]:
            self.fail("NO_CONTENT_VERIFIED_PHYSICAL_SOLANA_RUNTIME_SOURCE")
        print("[PASS] OSI-011C content-verified live Solana source boundary")
        print("[TRADER] Oracle now chooses its live tape from actual record structure, not filename guesses")
        print("[PASS] execution_authority=FALSE")
        print("[SCOPE] Source certification only; live intake must be re-observed afterward")

if __name__ == "__main__":
    unittest.main()
