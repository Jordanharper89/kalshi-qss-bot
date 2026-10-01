import json
import tempfile
import unittest
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_011_live_solana_source_boundary_certification import certify, write_report

ROOT = Path(__file__).resolve().parent

class TestOSI011D(unittest.TestCase):
    def test_coinbase_like_feed_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / "runtime" / "coinbase_hf"
            p.mkdir(parents=True)
            (p / "raw_events.jsonl").write_text(
                json.dumps({"timestamp":"2026-09-18T05:00:00+00:00","event":"ticker","price":150.0}) + "\n",
                encoding="utf-8",
            )
            result = certify(root)
            self.assertFalse(result["live_boundary_certified"])

    def test_solana_token_event_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / "runtime" / "anything"
            p.mkdir(parents=True)
            (p / "records.jsonl").write_text(
                json.dumps({
                    "mint":"So111",
                    "slot":123,
                    "signature":"abc",
                    "event_type":"swap",
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
        print("[NEAR_MATCH_COUNT]", result["near_match_count"])
        if result["live_sources"]:
            print("[TOP_SOURCE]", json.dumps(result["live_sources"][0], sort_keys=True))
        if result["near_match_examples"]:
            print("[TOP_NEAR_MATCH]", json.dumps(result["near_match_examples"][0], sort_keys=True))
        if not result["live_boundary_certified"]:
            self.fail("NO_STRICT_PHYSICAL_SOLANA_SOURCE_WITH_ASSET_TIME_EVENT")
        print("[PASS] OSI-011D strict Solana source boundary")
        print("[TRADER] Primary opportunity tape has token/pool identity plus time plus event/transaction evidence")
        print("[PASS] execution_authority=FALSE")
        print("[SCOPE] Coinbase/broader-market feeds remain evidence sources, not primary opportunity discovery")

if __name__ == "__main__":
    unittest.main()
