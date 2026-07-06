from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "historical_visibility_pattern_engine.py"
TEST = ROOT / "test_oi_139_historical_visibility_pattern_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-139 Historical Visibility Pattern Engine
Read-only Oracle Intelligence module.

Purpose:
- Analyze archive catalog/search outputs for recurring historical visibility patterns.
- Identify market, archive-type, tier, priority, and timing patterns.
- Produce pattern cards for downstream historical intelligence and market memory.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class HistoricalVisibilityPatternEngine:
    module = "oi_139_historical_visibility_pattern_engine"

    def __init__(self):
        self.last_pattern_report = {}

    def analyze_patterns(self, catalog_report=None, search_report=None):
        catalog_report = catalog_report or {}
        search_report = search_report or {}

        catalog_records = [x for x in catalog_report.get("catalog_records", []) if isinstance(x, dict)]
        search_results = [x for x in search_report.get("results", []) if isinstance(x, dict)]

        combined = self._combine_records(catalog_records, search_results)

        market_patterns = self._group_patterns(combined, "market", "market_visibility")
        type_patterns = self._group_patterns(combined, "archive_type", "archive_type_visibility")
        tier_patterns = self._group_patterns(combined, "catalog_tier", "tier_visibility")
        time_patterns = self._time_patterns(combined)

        patterns = market_patterns + type_patterns + tier_patterns + time_patterns
        patterns.sort(
            key=lambda x: (
                x["pattern_score"],
                x["record_count"],
                x["pattern_key"],
            ),
            reverse=True,
        )

        for idx, pattern in enumerate(patterns, start=1):
            pattern["pattern_rank"] = idx

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "execution_allowed": False,
            "input_modules": [
                "oi_137_q_series_visibility_archive_catalog_engine",
                "oi_138_archive_search_engine",
            ],
            "source_record_count": len(combined),
            "pattern_count": len(patterns),
            "patterns": patterns,
            "top_patterns": patterns[:10],
            "market_patterns": market_patterns,
            "archive_type_patterns": type_patterns,
            "tier_patterns": tier_patterns,
            "time_patterns": time_patterns,
            "pattern_summary": self._summary(patterns, combined),
            "qseries_handoff": {
                "execution_owner": "Q Series",
                "oracle_permission": "read_only",
                "execution_allowed": False,
                "handoff_type": "historical_visibility_patterns_only",
            },
        }

        self.last_pattern_report = report
        return report

    def _combine_records(self, catalog_records, search_results):
        records = {}
        for row in catalog_records + search_results:
            key = str(
                row.get("catalog_key")
                or row.get("archive_id")
                or row.get("receipt_id")
                or f"{row.get('market')}:{row.get('archive_type')}:{row.get('archive_timestamp')}"
            )
            if key not in records:
                records[key] = {}
            records[key].update(row)
            records[key]["catalog_key"] = key

        return list(records.values())

    def _group_patterns(self, records, field, pattern_type):
        grouped = {}

        for record in records:
            value = str(record.get(field) or "UNKNOWN")
            grouped.setdefault(value, []).append(record)

        patterns = []
        for key, rows in grouped.items():
            score = self._pattern_score(rows)
            patterns.append({
                "pattern_key": key,
                "pattern_type": pattern_type,
                "record_count": len(rows),
                "pattern_score": round(score, 4),
                "pattern_tier": self._tier(score),
                "avg_catalog_priority": round(self._avg(rows, "catalog_priority"), 4),
                "avg_visibility_score": round(self._avg(rows, "visibility_score"), 4),
                "avg_search_score": round(self._avg(rows, "search_score"), 4),
                "markets": self._unique(rows, "market"),
                "archive_types": self._unique(rows, "archive_type"),
                "catalog_tiers": self._unique(rows, "catalog_tier"),
                "pattern_note": self._note(key, pattern_type, score, len(rows)),
                "read_only": True,
                "execution_allowed": False,
            })

        return patterns

    def _time_patterns(self, records):
        buckets = {}

        for record in records:
            ts = self._float(record.get("archive_timestamp"), 0)
            bucket = self._time_bucket(ts)
            buckets.setdefault(bucket, []).append(record)

        patterns = []
        for bucket, rows in buckets.items():
            score = self._pattern_score(rows)
            patterns.append({
                "pattern_key": bucket,
                "pattern_type": "archive_time_visibility",
                "record_count": len(rows),
                "pattern_score": round(score, 4),
                "pattern_tier": self._tier(score),
                "avg_catalog_priority": round(self._avg(rows, "catalog_priority"), 4),
                "avg_visibility_score": round(self._avg(rows, "visibility_score"), 4),
                "avg_search_score": round(self._avg(rows, "search_score"), 4),
                "markets": self._unique(rows, "market"),
                "archive_types": self._unique(rows, "archive_type"),
                "catalog_tiers": self._unique(rows, "catalog_tier"),
                "pattern_note": self._note(bucket, "archive_time_visibility", score, len(rows)),
                "read_only": True,
                "execution_allowed": False,
            })

        return patterns

    def _pattern_score(self, rows):
        if not rows:
            return 0.0

        avg_priority = self._avg(rows, "catalog_priority")
        avg_visibility = self._avg(rows, "visibility_score")
        avg_search = self._avg(rows, "search_score")
        integrity = self._avg(rows, "integrity_score", default=100)
        frequency_boost = min(len(rows) * 4, 20)

        score = (
            avg_priority * 0.38
            + avg_visibility * 0.22
            + avg_search * 0.18
            + integrity * 0.12
            + frequency_boost
        )

        return max(0.0, min(100.0, score))

    def _tier(self, score):
        if score >= 85:
            return "dominant_pattern"
        if score >= 70:
            return "strong_pattern"
        if score >= 50:
            return "developing_pattern"
        if score >= 30:
            return "weak_pattern"
        return "archive_noise"

    def _note(self, key, pattern_type, score, count):
        return (
            f"{pattern_type} pattern '{key}' appears across {count} archived "
            f"visibility record(s) with pattern score {round(score, 2)}. "
            "This is read-only historical intelligence for Q Series context."
        )

    def _summary(self, patterns, records):
        tier_counts = {}
        type_counts = {}

        for pattern in patterns:
            tier = pattern["pattern_tier"]
            pattern_type = pattern["pattern_type"]
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            type_counts[pattern_type] = type_counts.get(pattern_type, 0) + 1

        top = patterns[0] if patterns else None

        return {
            "source_record_count": len(records),
            "pattern_count": len(patterns),
            "tier_counts": tier_counts,
            "pattern_type_counts": type_counts,
            "top_pattern_key": top["pattern_key"] if top else None,
            "top_pattern_type": top["pattern_type"] if top else None,
            "top_pattern_tier": top["pattern_tier"] if top else None,
            "dominant_pattern_count": tier_counts.get("dominant_pattern", 0),
            "execution_allowed": False,
            "read_only": True,
        }

    def _time_bucket(self, timestamp):
        if timestamp <= 0:
            return "unknown_time"
        if timestamp >= 1800000000:
            return "recent_archive_window"
        if timestamp >= 1700000000:
            return "mid_archive_window"
        return "deep_archive_window"

    def _unique(self, rows, field):
        values = []
        for row in rows:
            value = row.get(field)
            if value is not None and value not in values:
                values.append(value)
        return values

    def _avg(self, rows, field, default=0.0):
        values = []
        for row in rows:
            value = row.get(field)
            if value is None:
                continue
            values.append(self._float(value, default))

        if not values:
            return default

        return sum(values) / len(values)

    def _float(self, value, default=0.0):
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    def diagnostics(self):
        return {
            "module": self.module,
            "status": "ok",
            "has_pattern_report": bool(self.last_pattern_report),
            "pattern_count": self.last_pattern_report.get("pattern_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


historical_visibility_pattern_engine = HistoricalVisibilityPatternEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.historical_visibility_pattern_engine import (
    historical_visibility_pattern_engine,
)


def test_oi_139_historical_visibility_pattern_engine():
    catalog = {
        "catalog_records": [
            {
                "catalog_key": "arc-001",
                "archive_id": "arc-001",
                "market": "CRYPTO",
                "archive_type": "digest_snapshot",
                "archive_timestamp": 1800000000,
                "catalog_priority": 94,
                "catalog_tier": "institutional_priority",
                "visibility_score": 92,
                "integrity_score": 98,
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "catalog_key": "arc-002",
                "archive_id": "arc-002",
                "market": "NASDAQ",
                "archive_type": "strategic_briefing",
                "archive_timestamp": 1799999000,
                "catalog_priority": 76,
                "catalog_tier": "high_value",
                "visibility_score": 78,
                "integrity_score": 96,
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    search = {
        "results": [
            {
                "catalog_key": "arc-001",
                "archive_id": "arc-001",
                "market": "CRYPTO",
                "archive_type": "digest_snapshot",
                "archive_timestamp": 1800000000,
                "catalog_priority": 94,
                "catalog_tier": "institutional_priority",
                "search_score": 100,
                "read_only": True,
                "execution_allowed": False,
            }
        ]
    }

    report = historical_visibility_pattern_engine.analyze_patterns(catalog, search)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["source_record_count"] == 2
    assert report["pattern_count"] >= 4
    assert report["patterns"][0]["pattern_rank"] == 1
    assert report["patterns"][0]["execution_allowed"] is False
    assert report["patterns"][0]["read_only"] is True
    assert report["pattern_summary"]["execution_allowed"] is False
    assert report["pattern_summary"]["read_only"] is True
    assert report["market_patterns"]
    assert report["archive_type_patterns"]
    assert report["tier_patterns"]
    assert report["time_patterns"]

    diag = historical_visibility_pattern_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["pattern_count"] == report["pattern_count"]

    print("[PASS] OI-139 Historical Visibility Pattern Engine")
    print({
        "source_record_count": report["source_record_count"],
        "pattern_count": report["pattern_count"],
        "summary": report["pattern_summary"],
        "top": report["patterns"][0],
    })


if __name__ == "__main__":
    test_oi_139_historical_visibility_pattern_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .historical_visibility_pattern_engine import historical_visibility_pattern_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-139 INSTALLER")
print(" Historical Visibility Pattern Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-139 installed")
print()
print("Run:")
print("py test_oi_139_historical_visibility_pattern_engine.py")