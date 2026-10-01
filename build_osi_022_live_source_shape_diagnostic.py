from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
SUB = ROOT / "qseries_v2" / "oracle_strategy_intelligence" / "solana_intelligence"
MOD = SUB / "osi_022_live_source_shape_diagnostic.py"
TEST = ROOT / "test_osi_022_live_source_shape_diagnostic.py"

MOD_TEXT = r"""from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_012_live_event_normalization_and_intake import _read, normalize

def diagnose(root: Path, sample_limit: int = 100) -> dict:
    report_path = root / "OSI_011_LIVE_SOLANA_SOURCE_BOUNDARY.json"
    if not report_path.is_file():
        raise RuntimeError("Missing OSI-011 live source report")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    sources = []
    total_rows = 0
    normalized = 0
    failure_reasons = Counter()
    sample_shapes = []

    for src in report.get("live_sources", []):
        path = root / src["path"]
        rows = _read(path) if path.is_file() else []
        src_normalized = 0
        for row in rows[:sample_limit]:
            total_rows += 1
            if not isinstance(row, dict):
                failure_reasons["ROW_NOT_DICT"] += 1
                continue
            if len(sample_shapes) < 20:
                sample_shapes.append({
                    "source_path": src["path"],
                    "keys": sorted(row.keys()),
                    "sample": {k: row[k] for k in list(row.keys())[:20]},
                })
            event = normalize(row, src["path"])
            if event:
                normalized += 1
                src_normalized += 1
            else:
                has_asset = any(row.get(k) not in (None, "") for k in ("asset_key","mint","token_mint","address","pool_mint"))
                has_time = any(row.get(k) not in (None, "") for k in ("observed_at","timestamp","ts","created_at","block_time"))
                has_type = any(row.get(k) not in (None, "") for k in ("event_type","type","kind","event"))
                if not has_asset: failure_reasons["NO_RECOGNIZED_ASSET_FIELD"] += 1
                if not has_time: failure_reasons["NO_RECOGNIZED_TIME_FIELD"] += 1
                if not has_type: failure_reasons["NO_RECOGNIZED_EVENT_FIELD"] += 1
                if has_asset and has_time and has_type: failure_reasons["NORMALIZER_REJECTED_OTHER"] += 1
        sources.append({
            "path": src["path"],
            "rows_sampled": min(len(rows), sample_limit),
            "normalized_rows": src_normalized,
        })

    return {
        "revision": "OSI_022",
        "sources": sources,
        "rows_sampled_total": total_rows,
        "normalized_rows_total": normalized,
        "failure_reasons": dict(failure_reasons),
        "sample_shapes": sample_shapes,
        "execution_authority": False,
        "read_only": True,
    }

def write_report(root: Path) -> Path:
    data = diagnose(root)
    path = root / "OSI_022_LIVE_SOURCE_SHAPE_DIAGNOSTIC.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return path
"""

TEST_TEXT = r"""import json
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
"""

def main():
    print("=" * 112)
    print(" OSI-022 LIVE SOURCE SHAPE DIAGNOSTIC")
    print("=" * 112)
    required = [
        ROOT / "OSI_011_LIVE_SOLANA_SOURCE_BOUNDARY.json",
        ROOT / "qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_012_live_event_normalization_and_intake.py",
    ]
    for path in required:
        if not path.is_file():
            raise RuntimeError("Missing required certified boundary: " + str(path))
        print("[PASS] dependency:", path.relative_to(ROOT))
    SUB.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MOD_TEXT, encoding="utf-8")
    TEST.write_text(TEST_TEXT, encoding="utf-8")
    print("[PASS] installed:", MOD.relative_to(ROOT))
    print("[PASS] test:", TEST.name)
    print("[PASS] execution_authority=FALSE")
    print("[SCOPE] Read-only diagnosis of zero normalized live events")

if __name__ == "__main__":
    main()
