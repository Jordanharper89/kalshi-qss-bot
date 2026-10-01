from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUB = ROOT / "qseries_v2" / "oracle_strategy_intelligence" / "solana_intelligence"
MOD = SUB / "osi_011_live_solana_source_boundary_certification.py"
TEST = ROOT / "test_osi_011c_live_solana_source_boundary_certification.py"

MOD_TEXT = r"""from __future__ import annotations
import json
import time
from collections import Counter
from pathlib import Path

EXECUTION_AUTHORITY = False
READ_ONLY = True

ASSET_KEYS = {"asset_key","mint","token_mint","pool_mint","token","token_address","address","base_mint","quote_mint"}
TIME_KEYS = {"observed_at","timestamp","ts","created_at","block_time","blocktime","slot","updated_at"}
EVENT_KEYS = {"event_type","type","kind","event","instruction","program","signature","tx_signature","transaction_signature"}

def _rows(path: Path, limit: int = 60) -> list[dict]:
    rows = []
    try:
        if path.suffix.lower() == ".json":
            obj = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            values = obj if isinstance(obj, list) else [obj]
        else:
            values = []
            with path.open("r", encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh):
                    if i >= limit:
                        break
                    try:
                        values.append(json.loads(line))
                    except Exception:
                        pass
        for row in values[:limit]:
            if isinstance(row, dict):
                rows.append(row)
    except Exception:
        pass
    return rows

def _flatten_keys(value, depth: int = 0) -> set[str]:
    if depth > 4 or not isinstance(value, dict):
        return set()
    keys = {str(k).lower() for k in value.keys()}
    for child in value.values():
        if isinstance(child, dict):
            keys |= _flatten_keys(child, depth + 1)
        elif isinstance(child, list):
            for item in child[:5]:
                if isinstance(item, dict):
                    keys |= _flatten_keys(item, depth + 1)
    return keys

def _shape(rows: list[dict]) -> dict:
    hits = Counter()
    for row in rows:
        keys = _flatten_keys(row)
        if keys & ASSET_KEYS:
            hits["asset"] += 1
        if keys & TIME_KEYS:
            hits["time"] += 1
        if keys & EVENT_KEYS:
            hits["event"] += 1
    categories = sum(1 for k in ("asset","time","event") if hits[k] > 0)
    return {"categories": categories, "hits": dict(hits)}

def certify(root: Path, max_age_seconds: int = 3600) -> dict:
    now = time.time()
    accepted = []
    rejected = []

    search_roots = [root / "runtime_state", root / "runtime"]
    for base in search_roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in (".json",".jsonl"):
                continue
            age = now - path.stat().st_mtime
            if age > max_age_seconds:
                continue

            rows = _rows(path)
            shape = _shape(rows)

            # Content decides. Filename never certifies the source.
            if shape["categories"] < 2 or not rows:
                rejected.append({
                    "path": str(path.relative_to(root)),
                    "age_seconds": age,
                    "rows_sampled": len(rows),
                    "shape": shape,
                    "reason": "INSUFFICIENT_SOLANA_CONTENT_SHAPE",
                })
                continue

            accepted.append({
                "path": str(path.relative_to(root)),
                "age_seconds": age,
                "row_count": len(rows),
                "size": path.stat().st_size,
                "shape": shape,
            })

    accepted.sort(key=lambda x: (-x["shape"]["categories"], x["age_seconds"], x["path"]))

    return {
        "revision": "OSI_011C",
        "live_sources": accepted,
        "live_source_count": len(accepted),
        "live_boundary_certified": bool(accepted),
        "rejected_count": len(rejected),
        "rejected_examples": rejected[:75],
        "execution_authority": False,
        "read_only": True,
    }

def write_report(root: Path) -> Path:
    result = certify(root)
    path = root / "OSI_011_LIVE_SOLANA_SOURCE_BOUNDARY.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return path
"""

TEST_TEXT = r"""import json
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
"""

def main():
    print("=" * 112)
    print(" OSI-011C CONTENT-VERIFIED LIVE SOLANA SOURCE BOUNDARY")
    print("=" * 112)
    SUB.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MOD_TEXT, encoding="utf-8")
    TEST.write_text(TEST_TEXT, encoding="utf-8")
    print("[PASS] replaced:", MOD.relative_to(ROOT))
    print("[PASS] test:", TEST.name)
    print("[PASS] execution_authority=FALSE")
    print("[SCOPE] Direct replacement for failed OSI-011B; filenames no longer certify sources")

if __name__ == "__main__":
    main()
