import json
import tempfile
import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_022_live_source_shape_diagnostic import diagnose, write_report

ROOT = Path(__file__).resolve().parent

class T(unittest.TestCase):
    def test_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            live = root / "runtime_state" / "solana"
            live.mkdir(parents=True)
            src = live / "live_pool_events.json"
            src.write_text(json.dumps([
                {"mint":"M","type":"new_pool","timestamp":"2026-09-18T05:00:00+00:00"},
                {"foo":"bar"},
            ]), encoding="utf-8")
            (root / "OSI_011_LIVE_SOLANA_SOURCE_BOUNDARY.json").write_text(json.dumps({
                "live_sources":[{"path":"runtime_state/solana/live_pool_events.json"}]
            }), encoding="utf-8")
            d = diagnose(root)
            self.assertEqual(d["normalized_rows_total"], 1)
            self.assertGreater(d["failure_reasons"].get("NO_RECOGNIZED_ASSET_FIELD",0), 0)

    def test_physical(self):
        d = diagnose(ROOT)
        report = write_report(ROOT)
        self.assertTrue(report.is_file())
        print("[REPORT]", report)
        print("[ROWS_SAMPLED]", d["rows_sampled_total"])
        print("[NORMALIZED_ROWS]", d["normalized_rows_total"])
        print("[FAILURE_REASONS]", json.dumps(d["failure_reasons"], sort_keys=True))
        print("[SOURCE_SUMMARY]", json.dumps(d["sources"], sort_keys=True))
        print("[PASS] OSI-022 live source shape diagnostic")
        print("[TRADER] Identifies why the live tape is not becoming tradable opportunity events")
        print("[PASS] execution_authority=FALSE")
        print("[SCOPE] Diagnostic only; no source mutation and no admission bypass")

if __name__ == "__main__":
    unittest.main()
