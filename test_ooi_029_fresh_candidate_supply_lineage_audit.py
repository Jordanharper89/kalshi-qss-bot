import json
import tempfile
import unittest
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_029_fresh_candidate_supply_lineage_audit import audit, write_report

ROOT = Path(__file__).resolve().parent

class TestOOI029(unittest.TestCase):
    def test_deterministic_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pkg = root / "qseries_v2" / "oracle_strategy_intelligence" / "oracle_opportunity_intelligence"
            pkg.mkdir(parents=True)
            (root / "run_slop_buy_pressure_live.py").write_text(
                'THESIS="BUY_PRESSURE"\noutput="predictions.json"\n', encoding="utf-8"
            )
            (pkg / "ooi_026_registered_child_observation.py").write_text(
                'source_prediction_count=203\nfresh_candidates=0\nexpired_skipped=182\nresolved_skipped=21\n',
                encoding="utf-8",
            )
            status_dir = root / "runtime_state" / "oracle_opportunity_intelligence"
            status_dir.mkdir(parents=True)
            (status_dir / "registered_child_status.json").write_text(json.dumps({
                "state": "PRODUCER_AND_OBSERVER_HEALTHY",
                "round_count": 6,
                "execution_authority": False,
                "observation": {
                    "source_prediction_count": 203,
                    "fresh_candidates": 0,
                    "expired_skipped": 182,
                    "resolved_skipped": 21,
                    "future_skipped": 0,
                },
            }), encoding="utf-8")
            result = audit(root)
            self.assertEqual(result["supply_state"], "NO_FRESH_SUPPLY")
            self.assertTrue(result["prediction_accounting_exact"])
            self.assertEqual(result["accounted_predictions"], 203)
            self.assertFalse(result["execution_authority"])

    def test_physical_repo_audit(self):
        result = audit(ROOT)
        self.assertFalse(result["execution_authority"])
        self.assertTrue(result["read_only"])
        self.assertTrue(result["prediction_accounting_exact"])
        report = write_report(ROOT)
        self.assertTrue(report.is_file())
        print("[REPORT]", report)
        print("[SUPPLY_STATE]", result["supply_state"])
        print("[COUNTS]", json.dumps({
            "source": result["source_prediction_count"],
            "fresh": result["fresh_candidates"],
            "expired": result["expired_skipped"],
            "resolved": result["resolved_skipped"],
            "future": result["future_skipped"],
        }, sort_keys=True))
        print("[PASS] OOI-029 fresh-candidate supply lineage audit; execution_authority=FALSE")
        print("[SCOPE] Audit only; no freshness bypass, no producer mutation, no profitability claim")

if __name__ == "__main__":
    unittest.main()
