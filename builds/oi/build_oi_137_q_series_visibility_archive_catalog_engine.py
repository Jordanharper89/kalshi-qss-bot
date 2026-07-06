from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "q_series_visibility_archive_catalog_engine.py"
TEST = ROOT / "test_oi_137_q_series_visibility_archive_catalog_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-137 Q Series Visibility Archive Catalog Engine
Read-only Oracle Intelligence module.

Purpose:
- Build a searchable catalog from Oracle visibility/archive/index outputs.
- Normalize archive receipts, index entries, release records, and visibility events.
- Produce catalog records for historical intelligence lookup.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class QSeriesVisibilityArchiveCatalogEngine:
    module = "oi_137_q_series_visibility_archive_catalog_engine"

    def __init__(self):
        self.last_catalog = {}

    def build_catalog(
        self,
        archive_index_report=None,
        archive_receipt_report=None,
        visibility_report=None,
        release_report=None,
    ):
        archive_index_report = archive_index_report or {}
        archive_receipt_report = archive_receipt_report or {}
        visibility_report = visibility_report or {}
        release_report = release_report or {}

        index_entries = self._rows(
            archive_index_report,
            [
                "index_entries",
                "archive_index",
                "records",
                "items",
                "entries",
            ],
        )
        receipts = self._rows(
            archive_receipt_report,
            [
                "receipts",
                "archive_receipts",
                "records",
                "items",
                "entries",
            ],
        )
        visibility_events = self._rows(
            visibility_report,
            [
                "visibility_events",
                "events",
                "records",
                "items",
                "entries",
            ],
        )
        releases = self._rows(
            release_report,
            [
                "release_records",
                "releases",
                "records",
                "items",
                "entries",
            ],
        )

        receipt_index = self._index_by_key(receipts)
        visibility_index = self._index_by_key(visibility_events)
        release_index = self._index_by_key(releases)

        catalog_records = []

        for entry in index_entries:
            key = self._record_key(entry)
            receipt = receipt_index.get(key, {})
            visibility = visibility_index.get(key, {})
            release = release_index.get(key, {})

            record = self._catalog_record(entry, receipt, visibility, release)
            catalog_records.append(record)

        known_keys = {x["catalog_key"] for x in catalog_records}

        for source_name, rows in [
            ("receipt_only", receipts),
            ("visibility_only", visibility_events),
            ("release_only", releases),
        ]:
            for row in rows:
                key = self._record_key(row)
                if key in known_keys:
                    continue
                record = self._catalog_record(
                    row if source_name != "receipt_only" else {},
                    row if source_name == "receipt_only" else {},
                    row if source_name == "visibility_only" else {},
                    row if source_name == "release_only" else {},
                )
                record["source_note"] = source_name
                catalog_records.append(record)
                known_keys.add(key)

        catalog_records.sort(
            key=lambda x: (
                x["catalog_priority"],
                x["archive_timestamp"],
                x["catalog_key"],
            ),
            reverse=True,
        )

        for idx, record in enumerate(catalog_records, start=1):
            record["catalog_rank"] = idx

        catalog = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "execution_allowed": False,
            "input_modules": [
                "archive_index_layer",
                "archive_receipt_layer",
                "visibility_layer",
                "release_layer",
            ],
            "catalog_count": len(catalog_records),
            "catalog_records": catalog_records,
            "top_catalog_records": catalog_records[:10],
            "catalog_summary": self._summary(catalog_records),
            "qseries_handoff": {
                "execution_owner": "Q Series",
                "oracle_permission": "read_only",
                "execution_allowed": False,
                "handoff_type": "historical_visibility_catalog_only",
            },
        }

        self.last_catalog = catalog
        return catalog

    def _catalog_record(self, index_entry, receipt, visibility, release):
        merged = {}
        for row in [index_entry, receipt, visibility, release]:
            if isinstance(row, dict):
                merged.update(row)

        key = self._record_key(merged)

        market = str(
            merged.get("market")
            or merged.get("symbol")
            or merged.get("ticker")
            or merged.get("category")
            or "UNKNOWN"
        )

        archive_type = str(
            merged.get("archive_type")
            or merged.get("record_type")
            or merged.get("event_type")
            or merged.get("type")
            or "visibility_record"
        )

        timestamp = self._float(
            merged.get("archive_timestamp")
            or merged.get("timestamp")
            or merged.get("created_at")
            or merged.get("released_at")
            or 0
        )

        visibility_score = self._float(
            merged.get("visibility_score")
            or merged.get("score")
            or merged.get("confidence")
            or merged.get("priority")
            or 50
        )

        integrity_score = self._float(
            merged.get("integrity_score")
            or merged.get("validation_score")
            or merged.get("receipt_score")
            or 100
        )

        release_score = self._float(
            merged.get("release_score")
            or merged.get("release_confidence")
            or visibility_score
        )

        catalog_priority = self._catalog_priority(
            visibility_score=visibility_score,
            integrity_score=integrity_score,
            release_score=release_score,
            timestamp=timestamp,
        )

        return {
            "catalog_key": key,
            "market": market,
            "archive_type": archive_type,
            "archive_timestamp": timestamp,
            "catalog_priority": round(catalog_priority, 4),
            "catalog_tier": self._tier(catalog_priority),
            "visibility_score": round(visibility_score, 4),
            "integrity_score": round(integrity_score, 4),
            "release_score": round(release_score, 4),
            "receipt_id": merged.get("receipt_id") or merged.get("archive_receipt_id"),
            "archive_id": merged.get("archive_id") or merged.get("id") or key,
            "index_status": merged.get("index_status") or merged.get("status") or "cataloged",
            "visibility_status": merged.get("visibility_status") or merged.get("dashboard_status"),
            "release_status": merged.get("release_status"),
            "catalog_label": self._label(market, archive_type, catalog_priority),
            "catalog_summary": self._record_summary(market, archive_type, catalog_priority),
            "search_terms": self._search_terms(merged, market, archive_type, key),
            "read_only": True,
            "execution_allowed": False,
        }

    def _catalog_priority(self, visibility_score, integrity_score, release_score, timestamp):
        recency_component = min(max(timestamp, 0.0) / 10000000000.0, 10.0)
        score = (
            visibility_score * 0.42
            + integrity_score * 0.28
            + release_score * 0.20
            + recency_component
        )
        return max(0.0, min(100.0, score))

    def _tier(self, score):
        if score >= 85:
            return "institutional_priority"
        if score >= 70:
            return "high_value"
        if score >= 50:
            return "standard_catalog"
        if score >= 30:
            return "low_visibility"
        return "archive_only"

    def _label(self, market, archive_type, score):
        return f"{market} {archive_type} catalog record: {self._tier(score)}"

    def _record_summary(self, market, archive_type, score):
        return (
            f"{market} archive record classified as {archive_type} with catalog "
            f"priority {round(score, 2)}. This record is available for read-only "
            f"historical visibility search and Q Series context handoff."
        )

    def _search_terms(self, merged, market, archive_type, key):
        terms = {
            str(market).lower(),
            str(archive_type).lower(),
            str(key).lower(),
        }

        for field in [
            "label",
            "title",
            "headline",
            "summary",
            "archive_id",
            "receipt_id",
            "category",
            "market",
            "ticker",
            "symbol",
            "status",
        ]:
            value = merged.get(field)
            if value is not None:
                terms.add(str(value).lower())

        return sorted(x for x in terms if x and x != "none")

    def _summary(self, records):
        tier_counts = {}
        type_counts = {}
        market_counts = {}

        for record in records:
            tier = record["catalog_tier"]
            archive_type = record["archive_type"]
            market = record["market"]

            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            type_counts[archive_type] = type_counts.get(archive_type, 0) + 1
            market_counts[market] = market_counts.get(market, 0) + 1

        top = records[0] if records else None

        return {
            "tier_counts": tier_counts,
            "type_counts": type_counts,
            "market_counts": market_counts,
            "top_catalog_key": top["catalog_key"] if top else None,
            "top_market": top["market"] if top else None,
            "top_catalog_tier": top["catalog_tier"] if top else None,
            "institutional_priority_count": tier_counts.get("institutional_priority", 0),
            "execution_allowed": False,
            "read_only": True,
        }

    def _rows(self, report, keys):
        if isinstance(report, list):
            return [x for x in report if isinstance(x, dict)]

        if not isinstance(report, dict):
            return []

        for key in keys:
            value = report.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]

        return []

    def _index_by_key(self, rows):
        out = {}
        for row in rows:
            key = self._record_key(row)
            if key:
                out[key] = row
        return out

    def _record_key(self, row):
        if not isinstance(row, dict):
            return "UNKNOWN"

        key = (
            row.get("catalog_key")
            or row.get("archive_key")
            or row.get("archive_id")
            or row.get("receipt_id")
            or row.get("id")
        )

        if key:
            return str(key)

        market = str(row.get("market") or row.get("symbol") or row.get("ticker") or "UNKNOWN")
        record_type = str(row.get("archive_type") or row.get("type") or row.get("event_type") or "record")
        timestamp = str(row.get("archive_timestamp") or row.get("timestamp") or row.get("created_at") or "0")
        return f"{market}:{record_type}:{timestamp}"

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
            "has_catalog": bool(self.last_catalog),
            "catalog_count": self.last_catalog.get("catalog_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


q_series_visibility_archive_catalog_engine = QSeriesVisibilityArchiveCatalogEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.q_series_visibility_archive_catalog_engine import (
    q_series_visibility_archive_catalog_engine,
)


def test_oi_137_q_series_visibility_archive_catalog_engine():
    archive_index = {
        "index_entries": [
            {
                "archive_id": "arc-001",
                "market": "CRYPTO",
                "archive_type": "digest_snapshot",
                "archive_timestamp": 1800000000,
                "visibility_score": 92,
                "integrity_score": 98,
                "index_status": "indexed",
            },
            {
                "archive_id": "arc-002",
                "market": "NASDAQ",
                "archive_type": "strategic_briefing",
                "archive_timestamp": 1799999000,
                "visibility_score": 78,
                "integrity_score": 96,
                "index_status": "indexed",
            },
        ]
    }

    receipts = {
        "receipts": [
            {
                "archive_id": "arc-001",
                "receipt_id": "rec-001",
                "receipt_score": 99,
                "status": "receipt_verified",
            },
            {
                "archive_id": "arc-002",
                "receipt_id": "rec-002",
                "receipt_score": 95,
                "status": "receipt_verified",
            },
        ]
    }

    visibility = {
        "visibility_events": [
            {
                "archive_id": "arc-001",
                "visibility_status": "visible",
                "confidence": 94,
            },
            {
                "archive_id": "arc-002",
                "visibility_status": "visible",
                "confidence": 82,
            },
        ]
    }

    release = {
        "release_records": [
            {
                "archive_id": "arc-001",
                "release_status": "released",
                "release_score": 97,
            },
            {
                "archive_id": "arc-002",
                "release_status": "released",
                "release_score": 80,
            },
        ]
    }

    report = q_series_visibility_archive_catalog_engine.build_catalog(
        archive_index,
        receipts,
        visibility,
        release,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["catalog_count"] == 2
    assert report["catalog_records"][0]["catalog_rank"] == 1
    assert report["catalog_records"][0]["catalog_priority"] >= report["catalog_records"][-1]["catalog_priority"]
    assert report["catalog_records"][0]["execution_allowed"] is False
    assert report["catalog_records"][0]["read_only"] is True
    assert "crypto" in report["catalog_records"][0]["search_terms"]
    assert report["catalog_summary"]["execution_allowed"] is False
    assert report["catalog_summary"]["read_only"] is True

    diag = q_series_visibility_archive_catalog_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["catalog_count"] == report["catalog_count"]

    print("[PASS] OI-137 Q Series Visibility Archive Catalog Engine")
    print({
        "catalog_count": report["catalog_count"],
        "summary": report["catalog_summary"],
        "top": report["catalog_records"][0],
    })


if __name__ == "__main__":
    test_oi_137_q_series_visibility_archive_catalog_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .q_series_visibility_archive_catalog_engine import q_series_visibility_archive_catalog_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-137 INSTALLER")
print(" Q Series Visibility Archive Catalog Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-137 installed")
print()
print("Run:")
print("py test_oi_137_q_series_visibility_archive_catalog_engine.py")