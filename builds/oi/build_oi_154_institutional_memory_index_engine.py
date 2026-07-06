from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
MOD = PKG / "institutional_memory_index_engine.py"
TEST = ROOT / "test_oi_154_institutional_memory_index_engine.py"
INIT = PKG / "__init__.py"

MODULE = r'''"""
OI-154 — Oracle Institutional Memory Index Engine

Creates a read-only institutional memory index from Oracle historical
intelligence dashboard and manifest records.

Oracle never executes trades, manages positions, or submits orders.
Execution ownership remains with Q Series.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _stable_text(value: Any) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(f"{k}:{_stable_text(value[k])}" for k in sorted(value)) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_stable_text(v) for v in value) + "]"
    return repr(value)


def _hash(value: Any, size: int = 24) -> str:
    return sha256(_stable_text(value).encode("utf-8")).hexdigest()[:size]


@dataclass
class InstitutionalMemoryIndexRecord:
    memory_index_id: str
    source_id: str
    source_type: str
    market: str
    index_score: float
    memory_tier: str
    memory_status: str
    searchable_terms: List[str]
    lineage_hash: str
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    read_only: bool = True


@dataclass
class OracleInstitutionalMemoryIndexEngine:
    name: str = "oracle_institutional_memory_index_engine"
    version: str = "OI-154"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    index_schema_version: str = "institutional_memory_index_v1"
    supported_index_domains: List[str] = field(default_factory=lambda: [
        "PREDICTION_MARKETS",
        "CRYPTO",
        "STOCKS",
        "ETFS",
        "FUTURES",
        "COMMODITIES",
        "FOREX",
        "MACROECONOMICS",
        "WEATHER",
        "NEWS",
        "ALTERNATIVE_DATA",
    ])

    def classify_tier(self, score: float) -> str:
        if score >= 90:
            return "institutional_memory_index"
        if score >= 75:
            return "validated_memory_index"
        if score >= 60:
            return "review_memory_index"
        return "low_signal_memory_index"

    def classify_status(self, score: float) -> str:
        if score >= 90:
            return "executive_search_ready"
        if score >= 75:
            return "search_ready"
        if score >= 60:
            return "review_before_search"
        return "insufficient_memory_signal"

    def _extract_entries(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        source = _safe_dict(source)

        if isinstance(source.get("entries"), list):
            return _safe_list(source.get("entries"))

        tiles = _safe_dict(source.get("tiles"))
        if isinstance(tiles.get("top_entries"), list):
            return _safe_list(tiles.get("top_entries"))

        return []

    def _terms(self, item: Dict[str, Any]) -> List[str]:
        raw_terms = [
            item.get("source_id"),
            item.get("source_type"),
            item.get("record_type"),
            item.get("market"),
            item.get("domain"),
            item.get("manifest_tier"),
            item.get("manifest_status"),
            item.get("memory_tier"),
            item.get("memory_status"),
            item.get("confidence_tier"),
            item.get("timeline_phase"),
        ]

        terms: List[str] = []
        for term in raw_terms:
            if term is None:
                continue
            cleaned = str(term).strip().lower()
            if cleaned and cleaned not in terms:
                terms.append(cleaned)

        return terms

    def build_record(self, item: Dict[str, Any]) -> InstitutionalMemoryIndexRecord:
        item = _safe_dict(item)

        source_id = str(
            item.get("source_id")
            or item.get("manifest_entry_id")
            or item.get("ledger_entry_id")
            or item.get("ledger_id")
            or item.get("recall_id")
            or _hash(item, 12)
        )
        source_type = str(item.get("source_type") or item.get("record_type") or "historical_memory_record")
        market = str(item.get("market") or item.get("domain") or "UNKNOWN").upper()

        score = round(max(
            _num(item.get("index_score")),
            _num(item.get("historical_score")),
            _num(item.get("ledger_score")),
            _num(item.get("recall_score")),
            _num(item.get("confidence_score")),
            _num(item.get("receipt_score")),
        ), 2)

        lineage_payload = {
            "source_id": source_id,
            "source_type": source_type,
            "market": market,
            "score": score,
            "lineage": item.get("lineage_hash") or item.get("manifest_entry_id"),
        }

        return InstitutionalMemoryIndexRecord(
            memory_index_id=_hash(lineage_payload),
            source_id=source_id,
            source_type=source_type,
            market=market,
            index_score=score,
            memory_tier=self.classify_tier(score),
            memory_status=self.classify_status(score),
            searchable_terms=self._terms({**item, "source_id": source_id, "market": market, "source_type": source_type}),
            lineage_hash=_hash(lineage_payload),
            execution_allowed=False,
            execution_owner=self.execution_owner,
            read_only=True,
        )

    def build_index(self, source: Dict[str, Any]) -> Dict[str, Any]:
        entries = self._extract_entries(source)
        records = [self.build_record(entry) for entry in entries]
        records.sort(key=lambda r: r.index_score, reverse=True)

        market_counts: Dict[str, int] = {}
        tier_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}
        term_counts: Dict[str, int] = {}

        for record in records:
            market_counts[record.market] = market_counts.get(record.market, 0) + 1
            tier_counts[record.memory_tier] = tier_counts.get(record.memory_tier, 0) + 1
            status_counts[record.memory_status] = status_counts.get(record.memory_status, 0) + 1
            for term in record.searchable_terms:
                term_counts[term] = term_counts.get(term, 0) + 1

        top = records[0] if records else None
        index_id = _hash([record.__dict__ for record in records])

        return {
            "module": self.name,
            "version": self.version,
            "index_schema_version": self.index_schema_version,
            "memory_index_batch_id": index_id,
            "index_status": "memory_index_built" if records else "empty_memory_index",
            "created_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "universal_market_model_ready": True,
            "supported_index_domains": list(self.supported_index_domains),
            "source_manifest_id": source.get("manifest_id"),
            "source_dashboard_id": source.get("dashboard_id"),
            "record_count": len(records),
            "market_counts": market_counts,
            "tier_counts": tier_counts,
            "status_counts": status_counts,
            "term_counts": term_counts,
            "top_market": top.market if top else None,
            "top_memory_tier": top.memory_tier if top else None,
            "summary": {
                "headline": (
                    f"Institutional memory index built; top indexed market is {top.market}."
                    if top else
                    "Institutional memory index is empty."
                ),
                "memory_index_batch_id": index_id,
                "record_count": len(records),
                "top_market": top.market if top else None,
                "top_memory_tier": top.memory_tier if top else None,
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "records": [record.__dict__ for record in records],
        }

    def search_index(self, index: Dict[str, Any], query: str, limit: int = 10) -> Dict[str, Any]:
        query_terms = [term.strip().lower() for term in str(query or "").split() if term.strip()]
        records = _safe_list(_safe_dict(index).get("records"))

        matches: List[Dict[str, Any]] = []
        for record in records:
            record = _safe_dict(record)
            searchable_blob = " ".join(str(x).lower() for x in [
                record.get("source_id"),
                record.get("source_type"),
                record.get("market"),
                record.get("memory_tier"),
                record.get("memory_status"),
                " ".join(_safe_list(record.get("searchable_terms"))),
            ])
            if all(term in searchable_blob for term in query_terms):
                matches.append(record)

        matches.sort(key=lambda r: _num(r.get("index_score")), reverse=True)

        return {
            "module": self.name,
            "version": self.version,
            "query": query,
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
            "match_count": len(matches),
            "matches": matches[: max(0, int(limit))],
        }


oracle_institutional_memory_index_engine = OracleInstitutionalMemoryIndexEngine()
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.institutional_memory_index_engine import (
    oracle_institutional_memory_index_engine,
)


def test_index_builds_from_manifest_entries():
    manifest = {
        "manifest_id": "manifest-001",
        "entries": [
            {
                "source_id": "source-low",
                "source_type": "historical_case",
                "market": "STOCKS",
                "historical_score": 79.0,
                "manifest_tier": "validated_historical_manifest",
                "manifest_status": "validated_manifest",
            },
            {
                "source_id": "source-high",
                "source_type": "recall_ledger_entry",
                "market": "CRYPTO",
                "historical_score": 96.0,
                "manifest_tier": "institutional_historical_manifest",
                "manifest_status": "executive_ready_manifest",
            },
        ],
    }

    index = oracle_institutional_memory_index_engine.build_index(manifest)

    assert index["read_only"] is True
    assert index["execution_allowed"] is False
    assert index["execution_owner"] == "Q Series"
    assert index["source_manifest_id"] == "manifest-001"
    assert index["record_count"] == 2
    assert index["top_market"] == "CRYPTO"
    assert index["records"][0]["source_id"] == "source-high"
    assert index["records"][0]["memory_tier"] == "institutional_memory_index"


def test_index_builds_from_dashboard_top_entries():
    dashboard = {
        "dashboard_id": "hist-dash-001",
        "tiles": {
            "top_entries": [
                {
                    "source_id": "dash-source",
                    "source_type": "dashboard_manifest_entry",
                    "market": "FOREX",
                    "historical_score": 82.0,
                    "manifest_tier": "validated_historical_manifest",
                }
            ]
        },
    }

    index = oracle_institutional_memory_index_engine.build_index(dashboard)

    assert index["source_dashboard_id"] == "hist-dash-001"
    assert index["record_count"] == 1
    assert index["records"][0]["market"] == "FOREX"
    assert index["records"][0]["memory_status"] == "search_ready"


def test_search_index_returns_matching_records():
    manifest = {
        "manifest_id": "manifest-002",
        "entries": [
            {
                "source_id": "crypto-alpha",
                "source_type": "recall_ledger_entry",
                "market": "CRYPTO",
                "historical_score": 94.0,
                "manifest_tier": "institutional_historical_manifest",
            },
            {
                "source_id": "weather-beta",
                "source_type": "historical_case",
                "market": "WEATHER",
                "historical_score": 77.0,
                "manifest_tier": "validated_historical_manifest",
            },
        ],
    }

    index = oracle_institutional_memory_index_engine.build_index(manifest)
    results = oracle_institutional_memory_index_engine.search_index(index, "crypto institutional")

    assert results["read_only"] is True
    assert results["execution_allowed"] is False
    assert results["match_count"] == 1
    assert results["matches"][0]["source_id"] == "crypto-alpha"


def test_empty_index():
    index = oracle_institutional_memory_index_engine.build_index({"manifest_id": "empty", "entries": []})

    assert index["index_status"] == "empty_memory_index"
    assert index["record_count"] == 0
    assert index["records"] == []
    assert index["summary"]["read_only"] is True


if __name__ == "__main__":
    test_index_builds_from_manifest_entries()
    test_index_builds_from_dashboard_top_entries()
    test_search_index_returns_matching_records()
    test_empty_index()
    print("[PASS] OI-154 Oracle Institutional Memory Index Engine")
'''

def update_init():
    INIT.parent.mkdir(parents=True, exist_ok=True)
    content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    line = "from .institutional_memory_index_engine import oracle_institutional_memory_index_engine\n"
    if line not in content:
        content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OI-154 INSTALLER")
    print(" Oracle Institutional Memory Index Engine")
    print("=" * 40)

    PKG.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MODULE, encoding="utf-8")
    TEST.write_text(TEST_CODE, encoding="utf-8")
    update_init()

    print(f"[OK] Wrote {MOD}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print("\n[DONE] OI-154 installed")
    print("\nRun:")
    print("py test_oi_154_institutional_memory_index_engine.py")


if __name__ == "__main__":
    main()