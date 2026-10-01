from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
SUB = ROOT / "qseries_v2" / "oracle_strategy_intelligence" / "solana_intelligence"
MOD = SUB / "osi_011_live_solana_source_boundary_certification.py"
TEST = ROOT / "test_osi_011b_live_solana_source_boundary_certification.py"

MOD_TEXT = r"""from __future__ import annotations
import json
import re
import time
from collections import Counter
from pathlib import Path

EXECUTION_AUTHORITY = False
READ_ONLY = True

PATH_TERMS = (
    "solana", "mint", "swap", "liquidity", "wallet", "pool", "token",
)

CONTENT_TERMS = {
    "asset": {"asset_key","mint","token_mint","pool_mint","token","token_address","address"},
    "time": {"observed_at","timestamp","ts","created_at","block_time","blocktime","slot"},
    "event": {"event_type","type","kind","event","instruction","program","signature","tx_signature"},
}

def _path_term_match(path: Path) -> bool:
    text = str(path).lower().replace("\\\\","/")
    tokens = re.findall(r"[a-z0-9]+", text)
    return any(term in tokens for term in PATH_TERMS)

def _rows(path: Path, limit: int = 40) -> list[dict]:
    out = []
    try:
        if path.suffix.lower() == ".json":
            obj = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            values = obj if isinstance(obj, list) else [obj]
        else:
            values = []
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[:limit]:
                try:
                    values.append(json.loads(line))
                except Exception:
                    pass
        for row in values[:limit]:
            if isinstance(row, dict):
                out.append(row)
    except Exception:
        pass
    return out

def _flatten_keys(value, depth: int = 0) -> set[str]:
    if depth > 3 or not isinstance(value, dict):
        return set()
    keys = {str(k).lower() for k in value}
    for child in value.values():
        if isinstance(child, dict):
            keys |= _flatten_keys(child, depth + 1)
        elif isinstance(child, list):
            for item in child[:3]:
                if isinstance(item, dict):
                    keys |= _flatten_keys(item, depth + 1)
    return keys

def _content_score(rows: list[dict]) -> tuple[int, dict]:
    category_hits = Counter()
    for row in rows:
        keys = _flatten_keys(row)
        for category, terms in CONTENT_TERMS.items():
            if keys & terms:
                category_hits[category] += 1
    categories_present = sum(1 for c in CONTENT_TERMS if category_hits[c] > 0)
    score = categories_present
    return score, dict(category_hits)

def certify(root: Path, max_age_seconds: int = 900) -> dict:
    now = time.time()
    candidates = []
    rejected = []

    for base in (root / "runtime_state", root / "runtime"):
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in (".json",".jsonl"):
                continue

            age = now - path.stat().st_mtime
            if age > max_age_seconds:
                continue

            if not _path_term_match(path):
                rejected.append({
                    "path": str(path.relative_to(root)),
                    "reason": "NO_EXACT_SOLANA_PATH_TOKEN",
                })
                continue

            rows = _rows(path)
            score, category_hits = _content_score(rows)

            if score < 2:
                rejected.append({
                    "path": str(path.relative_to(root)),
                    "reason": "INSUFFICIENT_SOLANA_CONTENT_SHAPE",
                    "content_score": score,
                    "category_hits": category_hits,
                    "rows_sampled": len(rows),
                })
                continue

            candidates.append({
                "path": str(path.relative_to(root)),
                "age_seconds": age,
                "row_count": len(rows),
                "size": path.stat().st_size,
                "content_score": score,
                "category_hits": category_hits,
            })

    candidates.sort(key=lambda x: (-x["content_score"], x["age_seconds"], x["path"]))

    return {
        "revision": "OSI_011B",
        "live_sources": candidates,
        "live_source_count": len(candidates),
        "live_boundary_certified": bool(candidates),
        "rejected_count": len(rejected),
        "rejected_examples": rejected[:50],
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
"""

def main():
    print("=" * 112)
    print(" OSI-011B LIVE SOLANA SOURCE BOUNDARY REBUILD")
    print("=" * 112)
    SUB.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MOD_TEXT, encoding="utf-8")
    TEST.write_text(TEST_TEXT, encoding="utf-8")
    print("[PASS] replaced:", MOD.relative_to(ROOT))
    print("[PASS] test:", TEST.name)
    print("[PASS] execution_authority=FALSE")
    print("[SCOPE] Direct foundational repair; rejects 'spool' false-positive source selection")

if __name__ == "__main__":
    main()
