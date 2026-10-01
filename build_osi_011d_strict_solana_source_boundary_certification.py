 from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUB = ROOT / "qseries_v2" / "oracle_strategy_intelligence" / "solana_intelligence"
MOD = SUB / "osi_011_live_solana_source_boundary_certification.py"
TEST = ROOT / "test_osi_011d_strict_solana_source_boundary_certification.py"

MOD_TEXT = r"""from __future__ import annotations
import json
import time
from collections import Counter
from pathlib import Path

EXECUTION_AUTHORITY = False
READ_ONLY = True

ASSET_KEYS = {
    "asset_key","mint","token_mint","pool_mint","base_mint","quote_mint",
    "token_address","pool_address","pair_address","amm_address"
}
TIME_KEYS = {
    "observed_at","timestamp","ts","created_at","block_time","blocktime","slot","updated_at"
}
EVENT_KEYS = {
    "event_type","type","kind","event","instruction","program",
    "signature","tx_signature","transaction_signature"
}

def _rows(path: Path, limit: int = 80) -> list[dict]:
    out = []
    try:
        if path.suffix.lower() == ".json":
            obj = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            vals = obj if isinstance(obj, list) else [obj]
        else:
            vals = []
            with path.open("r", encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh):
                    if i >= limit:
                        break
                    try:
                        vals.append(json.loads(line))
                    except Exception:
                        pass
        out = [x for x in vals[:limit] if isinstance(x, dict)]
    except Exception:
        pass
    return out

def _flatten_keys(value, depth: int = 0) -> set[str]:
    if depth > 5 or not isinstance(value, dict):
        return set()
    keys = {str(k).lower() for k in value}
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
        if keys & ASSET_KEYS: hits["asset"] += 1
        if keys & TIME_KEYS: hits["time"] += 1
        if keys & EVENT_KEYS: hits["event"] += 1
    return {
        "asset_hits": hits["asset"],
        "time_hits": hits["time"],
        "event_hits": hits["event"],
        "strict_match": hits["asset"] > 0 and hits["time"] > 0 and hits["event"] > 0,
    }

def certify(root: Path, max_age_seconds: int = 7200) -> dict:
    now = time.time()
    accepted, near = [], []

    for base in (root / "runtime_state", root / "runtime"):
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in (".json",".jsonl"):
                continue
            age = now - path.stat().st_mtime
            if age > max_age_seconds:
                continue

            rows = _rows(path)
            if not rows:
                continue

            shape = _shape(rows)
            row = {
                "path": str(path.relative_to(root)),
                "age_seconds": age,
                "row_count": len(rows),
                "size": path.stat().st_size,
                "shape": shape,
            }

            if shape["strict_match"]:
                accepted.append(row)
            elif shape["asset_hits"] or shape["time_hits"] or shape["event_hits"]:
                near.append(row)

    accepted.sort(key=lambda x: (
        -x["shape"]["asset_hits"],
        -x["shape"]["event_hits"],
        -x["shape"]["time_hits"],
        x["age_seconds"],
        x["path"],
    ))
    near.sort(key=lambda x: (
        -(x["shape"]["asset_hits"] + x["shape"]["time_hits"] + x["shape"]["event_hits"]),
        x["age_seconds"],
        x["path"],
    ))

    return {
        "revision": "OSI_011D",
        "live_sources": accepted,
        "live_source_count": len(accepted),
        "live_boundary_certified": bool(accepted),
        "near_match_count": len(near),
        "near_match_examples": near[:50],
        "execution_authority": False,
        "read_only": True,
        "primary_source_requirement": "ASSET_IDENTITY + TIME + EVENT/TRANSACTION",
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
"""

def main():
    print("=" * 112)
    print(" OSI-011D STRICT SOLANA SOURCE BOUNDARY")
    print("=" * 112)
    SUB.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MOD_TEXT, encoding="utf-8")
    TEST.write_text(TEST_TEXT, encoding="utf-8")
    print("[PASS] replaced:", MOD.relative_to(ROOT))
    print("[PASS] test:", TEST.name)
    print("[PASS] execution_authority=FALSE")
    print("[SCOPE] Direct replacement for OSI-011C; rejects Coinbase-like feeds as primary Solana tape")

if __name__ == "__main__":
    main()
