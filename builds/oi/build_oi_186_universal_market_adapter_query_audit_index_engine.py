from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "universal_market_adapter_query_audit_index_engine.py"
TEST = ROOT / "test_oi_186_universal_market_adapter_query_audit_index_engine.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
"""
OI-186 — Oracle Universal Market Adapter Query Audit Index Engine

Read-only indexing layer for Universal Market Adapter query audit records.

This module organizes audit records produced by OI-185 into replayable,
explainable, telemetry-friendly lookup indexes. It never executes trades,
routes orders, submits orders, or manages positions.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional
import json


READ_ONLY_GUARDRAILS = {
    "oracle_read_only": True,
    "executes_trades": False,
    "routes_orders": False,
    "submits_orders": False,
    "manages_positions": False,
    "execution_owner": "Q_SERIES_ONLY",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _hash(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _safe_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict"):
        converted = value.to_dict()
        if isinstance(converted, Mapping):
            return dict(converted)
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {"value": value}


@dataclass(frozen=True)
class QueryAuditIndexEntry:
    audit_id: str
    adapter_id: str
    query_id: str
    replay_key: str
    passed: bool
    query_hash: str
    resolver_hash: str
    market_model_hash: str
    finding_codes: List[str]
    created_at: str
    indexed_at: str
    source_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QueryAuditIndexResult:
    index_id: str
    created_at: str
    entry_count: int
    passed_count: int
    failed_count: int
    adapter_count: int
    query_count: int
    replay_key_count: int
    integrity_hash: str
    read_only_guardrails: Dict[str, Any]
    telemetry: Dict[str, Any]
    explainability: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UniversalMarketAdapterQueryAuditIndexEngine:
    """
    Builds read-only institutional indexes from adapter query audit records.
    """

    module_id = "OI-186"
    module_name = "Oracle Universal Market Adapter Query Audit Index Engine"

    def __init__(self, oracle_instance_id: str = "oracle.default") -> None:
        self.oracle_instance_id = oracle_instance_id
        self._entries: Dict[str, QueryAuditIndexEntry] = {}
        self._by_adapter: Dict[str, List[str]] = {}
        self._by_query: Dict[str, List[str]] = {}
        self._by_replay_key: Dict[str, str] = {}
        self._by_status: Dict[str, List[str]] = {"passed": [], "failed": []}
        self._by_finding_code: Dict[str, List[str]] = {}

    def index_record(self, record: Any) -> QueryAuditIndexEntry:
        data = self._record_to_dict(record)

        audit_id = str(data.get("audit_id") or data.get("id") or "").strip()
        if not audit_id:
            audit_id = "audit." + _hash(data)[:24]

        adapter_id = str(data.get("adapter_id") or "unknown.adapter").strip()
        query_id = str(data.get("query_id") or "unknown.query").strip()
        replay_key = str(data.get("replay_key") or _hash({"audit_id": audit_id, "adapter_id": adapter_id, "query_id": query_id}))

        passed = bool(data.get("passed", False))
        findings = data.get("findings") or []
        finding_codes = self._extract_finding_codes(findings)

        entry = QueryAuditIndexEntry(
            audit_id=audit_id,
            adapter_id=adapter_id,
            query_id=query_id,
            replay_key=replay_key,
            passed=passed,
            query_hash=str(data.get("query_hash") or ""),
            resolver_hash=str(data.get("resolver_hash") or ""),
            market_model_hash=str(data.get("market_model_hash") or ""),
            finding_codes=finding_codes,
            created_at=str(data.get("created_at") or ""),
            indexed_at=_utc_now(),
            source_hash=_hash(data),
        )

        self._upsert(entry)
        return entry

    def index_records(self, records: Iterable[Any]) -> QueryAuditIndexResult:
        for record in records:
            self.index_record(record)
        return self.index_summary()

    def lookup_by_audit_id(self, audit_id: str) -> Optional[QueryAuditIndexEntry]:
        return self._entries.get(str(audit_id))

    def lookup_by_replay_key(self, replay_key: str) -> Optional[QueryAuditIndexEntry]:
        audit_id = self._by_replay_key.get(str(replay_key))
        return self._entries.get(audit_id) if audit_id else None

    def lookup_by_adapter(self, adapter_id: str) -> List[QueryAuditIndexEntry]:
        return [self._entries[audit_id] for audit_id in self._by_adapter.get(str(adapter_id), [])]

    def lookup_by_query(self, query_id: str) -> List[QueryAuditIndexEntry]:
        return [self._entries[audit_id] for audit_id in self._by_query.get(str(query_id), [])]

    def lookup_failed(self) -> List[QueryAuditIndexEntry]:
        return [self._entries[audit_id] for audit_id in self._by_status["failed"]]

    def lookup_passed(self) -> List[QueryAuditIndexEntry]:
        return [self._entries[audit_id] for audit_id in self._by_status["passed"]]

    def lookup_by_finding_code(self, finding_code: str) -> List[QueryAuditIndexEntry]:
        return [self._entries[audit_id] for audit_id in self._by_finding_code.get(str(finding_code), [])]

    def entries(self) -> List[QueryAuditIndexEntry]:
        return list(self._entries.values())

    def index_summary(self) -> QueryAuditIndexResult:
        entries = self.entries()
        passed_count = sum(1 for entry in entries if entry.passed)
        failed_count = len(entries) - passed_count

        integrity_payload = [
            {
                "audit_id": entry.audit_id,
                "adapter_id": entry.adapter_id,
                "query_id": entry.query_id,
                "replay_key": entry.replay_key,
                "passed": entry.passed,
                "source_hash": entry.source_hash,
            }
            for entry in sorted(entries, key=lambda item: item.audit_id)
        ]

        integrity_hash = _hash(integrity_payload)

        return QueryAuditIndexResult(
            index_id="oi186.index." + integrity_hash[:24],
            created_at=_utc_now(),
            entry_count=len(entries),
            passed_count=passed_count,
            failed_count=failed_count,
            adapter_count=len(self._by_adapter),
            query_count=len(self._by_query),
            replay_key_count=len(self._by_replay_key),
            integrity_hash=integrity_hash,
            read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
            telemetry={
                "module_id": self.module_id,
                "module_name": self.module_name,
                "oracle_instance_id": self.oracle_instance_id,
                "entry_count": len(entries),
                "passed_count": passed_count,
                "failed_count": failed_count,
                "finding_code_count": len(self._by_finding_code),
                "latest_indexed_at": entries[-1].indexed_at if entries else None,
            },
            explainability={
                "purpose": "Index query audit records for replay, traceability, and institutional lookup.",
                "read_only_reason": "Indexing audit records does not create execution authority.",
                "lookup_dimensions": [
                    "audit_id",
                    "adapter_id",
                    "query_id",
                    "replay_key",
                    "status",
                    "finding_code",
                ],
                "integrity_method": "Deterministic SHA-256 hash over sorted index entries.",
                "execution_boundary": "Q Series remains the only execution engine.",
            },
        )

    def replay_manifest(self) -> Dict[str, Any]:
        summary = self.index_summary()
        return {
            "module_id": self.module_id,
            "oracle_instance_id": self.oracle_instance_id,
            "index_id": summary.index_id,
            "integrity_hash": summary.integrity_hash,
            "entries": [
                {
                    "audit_id": entry.audit_id,
                    "adapter_id": entry.adapter_id,
                    "query_id": entry.query_id,
                    "replay_key": entry.replay_key,
                    "source_hash": entry.source_hash,
                    "passed": entry.passed,
                }
                for entry in sorted(self.entries(), key=lambda item: item.audit_id)
            ],
        }

    def _upsert(self, entry: QueryAuditIndexEntry) -> None:
        if entry.audit_id in self._entries:
            self._remove_from_indexes(self._entries[entry.audit_id])

        self._entries[entry.audit_id] = entry
        self._by_adapter.setdefault(entry.adapter_id, []).append(entry.audit_id)
        self._by_query.setdefault(entry.query_id, []).append(entry.audit_id)
        self._by_replay_key[entry.replay_key] = entry.audit_id
        self._by_status["passed" if entry.passed else "failed"].append(entry.audit_id)

        for code in entry.finding_codes:
            self._by_finding_code.setdefault(code, []).append(entry.audit_id)

    def _remove_from_indexes(self, entry: QueryAuditIndexEntry) -> None:
        for index in (self._by_adapter, self._by_query, self._by_finding_code):
            for key in list(index.keys()):
                index[key] = [audit_id for audit_id in index[key] if audit_id != entry.audit_id]
                if not index[key]:
                    del index[key]

        for status in ("passed", "failed"):
            self._by_status[status] = [audit_id for audit_id in self._by_status[status] if audit_id != entry.audit_id]

        if self._by_replay_key.get(entry.replay_key) == entry.audit_id:
            del self._by_replay_key[entry.replay_key]

    def _record_to_dict(self, record: Any) -> Dict[str, Any]:
        if hasattr(record, "to_dict"):
            converted = record.to_dict()
            if isinstance(converted, Mapping):
                return dict(converted)
        return _safe_dict(record)

    def _extract_finding_codes(self, findings: Any) -> List[str]:
        codes: List[str] = []
        if not isinstance(findings, list):
            return codes

        for finding in findings:
            data = _safe_dict(finding)
            code = data.get("code")
            if code:
                codes.append(str(code))
        return codes


def create_query_audit_index_engine(
    oracle_instance_id: str = "oracle.default",
) -> UniversalMarketAdapterQueryAuditIndexEngine:
    return UniversalMarketAdapterQueryAuditIndexEngine(oracle_instance_id=oracle_instance_id)


__all__ = [
    "READ_ONLY_GUARDRAILS",
    "QueryAuditIndexEntry",
    "QueryAuditIndexResult",
    "UniversalMarketAdapterQueryAuditIndexEngine",
    "create_query_audit_index_engine",
]
'''.lstrip(), encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_query_audit_index_engine import (
    READ_ONLY_GUARDRAILS,
    UniversalMarketAdapterQueryAuditIndexEngine,
    create_query_audit_index_engine,
)


def test_oi_186_query_audit_index_engine():
    engine = create_query_audit_index_engine("oracle.test")

    records = [
        {
            "audit_id": "audit-001",
            "created_at": "2026-01-01T00:00:00+00:00",
            "adapter_id": "adp.kalshi",
            "query_id": "q-001",
            "replay_key": "replay-001",
            "passed": True,
            "query_hash": "a" * 64,
            "resolver_hash": "b" * 64,
            "market_model_hash": "c" * 64,
            "findings": [],
        },
        {
            "audit_id": "audit-002",
            "created_at": "2026-01-01T00:01:00+00:00",
            "adapter_id": "adp.kalshi",
            "query_id": "q-002",
            "replay_key": "replay-002",
            "passed": False,
            "query_hash": "d" * 64,
            "resolver_hash": "e" * 64,
            "market_model_hash": "f" * 64,
            "findings": [
                {
                    "code": "EXECUTION_BOUNDARY_VIOLATION",
                    "severity": "critical",
                    "message": "Execution boundary crossed.",
                }
            ],
        },
        {
            "audit_id": "audit-003",
            "created_at": "2026-01-01T00:02:00+00:00",
            "adapter_id": "adp.polymarket",
            "query_id": "q-001",
            "replay_key": "replay-003",
            "passed": True,
            "query_hash": "g" * 64,
            "resolver_hash": "h" * 64,
            "market_model_hash": "i" * 64,
            "findings": [
                {
                    "code": "TELEMETRY_MINIMAL",
                    "severity": "info",
                    "message": "Minimal telemetry.",
                }
            ],
        },
    ]

    summary = engine.index_records(records)

    assert summary.entry_count == 3
    assert summary.passed_count == 2
    assert summary.failed_count == 1
    assert summary.adapter_count == 2
    assert summary.query_count == 2
    assert summary.replay_key_count == 3
    assert len(summary.integrity_hash) == 64
    assert summary.read_only_guardrails == READ_ONLY_GUARDRAILS
    assert summary.telemetry["oracle_instance_id"] == "oracle.test"

    assert engine.lookup_by_audit_id("audit-001").query_id == "q-001"
    assert engine.lookup_by_replay_key("replay-002").audit_id == "audit-002"
    assert len(engine.lookup_by_adapter("adp.kalshi")) == 2
    assert len(engine.lookup_by_query("q-001")) == 2
    assert len(engine.lookup_failed()) == 1
    assert len(engine.lookup_passed()) == 2

    boundary = engine.lookup_by_finding_code("EXECUTION_BOUNDARY_VIOLATION")
    assert len(boundary) == 1
    assert boundary[0].audit_id == "audit-002"

    manifest = engine.replay_manifest()
    assert manifest["module_id"] == "OI-186"
    assert manifest["index_id"] == summary.index_id
    assert len(manifest["entries"]) == 3

    engine.index_record({
        "audit_id": "audit-002",
        "adapter_id": "adp.kalshi",
        "query_id": "q-002",
        "replay_key": "replay-002b",
        "passed": True,
        "findings": [],
    })

    updated = engine.index_summary()
    assert updated.entry_count == 3
    assert updated.failed_count == 0
    assert engine.lookup_by_replay_key("replay-002") is None
    assert engine.lookup_by_replay_key("replay-002b").passed is True


if __name__ == "__main__":
    test_oi_186_query_audit_index_engine()
    print("[PASS] OI-186 Universal Market Adapter Query Audit Index Engine")
'''.lstrip(), encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

import_line = "from .universal_market_adapter_query_audit_index_engine import UniversalMarketAdapterQueryAuditIndexEngine, create_query_audit_index_engine\n"
if import_line not in init_text:
    init_text += ("\n" if init_text and not init_text.endswith("\n") else "") + import_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-186 INSTALLER")
print(" Universal Market Adapter Query Audit Index Engine")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-186 installed")
print()
print("Run:")
print("py test_oi_186_universal_market_adapter_query_audit_index_engine.py")