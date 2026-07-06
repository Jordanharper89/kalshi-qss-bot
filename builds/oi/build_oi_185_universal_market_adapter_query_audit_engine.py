from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "universal_market_adapter_query_audit_engine.py"
TEST = ROOT / "test_oi_185_universal_market_adapter_query_audit_engine.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
"""
OI-185 — Oracle Universal Market Adapter Query Audit Engine

Read-only institutional audit layer for Universal Market Adapter query
resolution events.

This engine does not execute trades, route orders, manage positions, or mutate
market state. It audits adapter query resolver outputs for traceability,
replayability, explainability, governance, and telemetry.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple
import json
import uuid


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
class QueryAuditFinding:
    code: str
    severity: str
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QueryAuditRecord:
    audit_id: str
    created_at: str
    adapter_id: str
    query_id: str
    query_hash: str
    resolver_hash: str
    market_model_hash: str
    replay_key: str
    read_only_guardrails: Dict[str, Any]
    telemetry: Dict[str, Any]
    findings: List[QueryAuditFinding]
    explainability: Dict[str, Any]

    @property
    def passed(self) -> bool:
        return not any(f.severity in {"error", "critical"} for f in self.findings)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["passed"] = self.passed
        return data


class UniversalMarketAdapterQueryAuditEngine:
    """
    Audits Universal Market Adapter query resolver activity.

    The component is intentionally read-only and produces immutable audit records
    suitable for replay, telemetry, governance, and architecture registry review.
    """

    module_id = "OI-185"
    module_name = "Oracle Universal Market Adapter Query Audit Engine"

    def __init__(self, oracle_instance_id: str = "oracle.default") -> None:
        self.oracle_instance_id = oracle_instance_id
        self._records: List[QueryAuditRecord] = []

    def audit_query(
        self,
        *,
        adapter_id: str,
        query: Mapping[str, Any],
        resolver_output: Mapping[str, Any],
        market_model: Optional[Mapping[str, Any]] = None,
        telemetry: Optional[Mapping[str, Any]] = None,
        context: Optional[Mapping[str, Any]] = None,
    ) -> QueryAuditRecord:
        adapter_id = str(adapter_id or "").strip()
        query_dict = _safe_dict(query)
        resolver_dict = _safe_dict(resolver_output)
        market_model_dict = _safe_dict(market_model)
        telemetry_dict = _safe_dict(telemetry)
        context_dict = _safe_dict(context)

        query_id = str(
            query_dict.get("query_id")
            or resolver_dict.get("query_id")
            or context_dict.get("query_id")
            or f"query.{uuid.uuid4().hex}"
        )

        findings = self._evaluate(
            adapter_id=adapter_id,
            query=query_dict,
            resolver_output=resolver_dict,
            market_model=market_model_dict,
            telemetry=telemetry_dict,
        )

        query_hash = _hash(query_dict)
        resolver_hash = _hash(resolver_dict)
        market_model_hash = _hash(market_model_dict)
        replay_key = _hash(
            {
                "oracle_instance_id": self.oracle_instance_id,
                "adapter_id": adapter_id,
                "query_id": query_id,
                "query_hash": query_hash,
                "resolver_hash": resolver_hash,
                "market_model_hash": market_model_hash,
            }
        )

        record = QueryAuditRecord(
            audit_id=f"oi185.audit.{uuid.uuid4().hex}",
            created_at=_utc_now(),
            adapter_id=adapter_id,
            query_id=query_id,
            query_hash=query_hash,
            resolver_hash=resolver_hash,
            market_model_hash=market_model_hash,
            replay_key=replay_key,
            read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
            telemetry={
                "oracle_instance_id": self.oracle_instance_id,
                "module_id": self.module_id,
                "module_name": self.module_name,
                "adapter_id": adapter_id,
                "query_id": query_id,
                "finding_count": len(findings),
                "error_count": sum(1 for f in findings if f.severity in {"error", "critical"}),
                **telemetry_dict,
            },
            findings=findings,
            explainability={
                "purpose": "Audit adapter query resolution without execution authority.",
                "read_only_reason": "Oracle Intelligence produces intelligence only; Q Series owns execution.",
                "replay_inputs": {
                    "adapter_id": adapter_id,
                    "query_hash": query_hash,
                    "resolver_hash": resolver_hash,
                    "market_model_hash": market_model_hash,
                },
                "checks": [
                    "adapter identity",
                    "query structure",
                    "resolver output structure",
                    "Universal Market Model compatibility",
                    "execution-boundary violations",
                    "telemetry completeness",
                    "replay determinism",
                ],
            },
        )

        self._records.append(record)
        return record

    def audit_many(
        self,
        events: Iterable[Mapping[str, Any]],
    ) -> List[QueryAuditRecord]:
        records: List[QueryAuditRecord] = []
        for event in events:
            event_dict = _safe_dict(event)
            records.append(
                self.audit_query(
                    adapter_id=event_dict.get("adapter_id", ""),
                    query=_safe_dict(event_dict.get("query")),
                    resolver_output=_safe_dict(event_dict.get("resolver_output")),
                    market_model=_safe_dict(event_dict.get("market_model")),
                    telemetry=_safe_dict(event_dict.get("telemetry")),
                    context=_safe_dict(event_dict.get("context")),
                )
            )
        return records

    def records(self) -> List[QueryAuditRecord]:
        return list(self._records)

    def telemetry_snapshot(self) -> Dict[str, Any]:
        total = len(self._records)
        failed = sum(1 for r in self._records if not r.passed)
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "oracle_instance_id": self.oracle_instance_id,
            "records": total,
            "passed": total - failed,
            "failed": failed,
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
            "latest_replay_key": self._records[-1].replay_key if self._records else None,
        }

    def replay_manifest(self) -> Dict[str, Any]:
        return {
            "module_id": self.module_id,
            "oracle_instance_id": self.oracle_instance_id,
            "record_count": len(self._records),
            "records": [
                {
                    "audit_id": r.audit_id,
                    "adapter_id": r.adapter_id,
                    "query_id": r.query_id,
                    "query_hash": r.query_hash,
                    "resolver_hash": r.resolver_hash,
                    "market_model_hash": r.market_model_hash,
                    "replay_key": r.replay_key,
                    "passed": r.passed,
                }
                for r in self._records
            ],
        }

    def _evaluate(
        self,
        *,
        adapter_id: str,
        query: Dict[str, Any],
        resolver_output: Dict[str, Any],
        market_model: Dict[str, Any],
        telemetry: Dict[str, Any],
    ) -> List[QueryAuditFinding]:
        findings: List[QueryAuditFinding] = []

        if not adapter_id:
            findings.append(QueryAuditFinding(
                code="ADAPTER_ID_MISSING",
                severity="error",
                message="Adapter identity is required for institutional query audit.",
            ))

        if not query:
            findings.append(QueryAuditFinding(
                code="QUERY_MISSING",
                severity="error",
                message="Query payload is missing.",
            ))

        if not resolver_output:
            findings.append(QueryAuditFinding(
                code="RESOLVER_OUTPUT_MISSING",
                severity="error",
                message="Resolver output is missing.",
            ))

        if query and "market_type" not in query and "market" not in query:
            findings.append(QueryAuditFinding(
                code="QUERY_MARKET_CONTEXT_WEAK",
                severity="warning",
                message="Query does not explicitly declare market_type or market.",
                evidence={"query_keys": sorted(query.keys())},
            ))

        if resolver_output and not any(k in resolver_output for k in ("resolved", "result", "markets", "adapter_result")):
            findings.append(QueryAuditFinding(
                code="RESOLVER_RESULT_SHAPE_UNKNOWN",
                severity="warning",
                message="Resolver output lacks a recognized result field.",
                evidence={"resolver_keys": sorted(resolver_output.keys())},
            ))

        execution_terms = {
            "execute", "executed", "submit_order", "route_order", "order",
            "trade", "position", "fill", "buy", "sell"
        }
        flattened = _stable_json({"query": query, "resolver_output": resolver_output}).lower()
        detected = sorted(term for term in execution_terms if term in flattened)
        if detected:
            findings.append(QueryAuditFinding(
                code="EXECUTION_BOUNDARY_REVIEW",
                severity="warning",
                message="Execution-like terms detected. Oracle must remain read-only.",
                evidence={"detected_terms": detected},
            ))

        explicit_execution_flags = [
            key for key, value in resolver_output.items()
            if key in {"executed", "order_submitted", "position_opened", "trade_routed"} and bool(value)
        ]
        if explicit_execution_flags:
            findings.append(QueryAuditFinding(
                code="EXECUTION_BOUNDARY_VIOLATION",
                severity="critical",
                message="Resolver output indicates execution behavior, which Oracle is forbidden to perform.",
                evidence={"flags": explicit_execution_flags},
            ))

        if market_model:
            if not any(k in market_model for k in ("universal_market_id", "market_id", "market_type", "schema_version")):
                findings.append(QueryAuditFinding(
                    code="UNIVERSAL_MARKET_MODEL_WEAK",
                    severity="warning",
                    message="Market model payload does not expose common Universal Market Model identifiers.",
                    evidence={"market_model_keys": sorted(market_model.keys())},
                ))
        else:
            findings.append(QueryAuditFinding(
                code="MARKET_MODEL_NOT_ATTACHED",
                severity="warning",
                message="No Universal Market Model payload attached to audit event.",
            ))

        if not telemetry:
            findings.append(QueryAuditFinding(
                code="TELEMETRY_MINIMAL",
                severity="info",
                message="No upstream telemetry was supplied; audit telemetry was generated locally.",
            ))

        return findings


def create_query_audit_engine(oracle_instance_id: str = "oracle.default") -> UniversalMarketAdapterQueryAuditEngine:
    return UniversalMarketAdapterQueryAuditEngine(oracle_instance_id=oracle_instance_id)


__all__ = [
    "READ_ONLY_GUARDRAILS",
    "QueryAuditFinding",
    "QueryAuditRecord",
    "UniversalMarketAdapterQueryAuditEngine",
    "create_query_audit_engine",
]
'''.lstrip(), encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_query_audit_engine import (
    READ_ONLY_GUARDRAILS,
    UniversalMarketAdapterQueryAuditEngine,
    create_query_audit_engine,
)


def test_oi_185_query_audit_engine():
    engine = create_query_audit_engine("oracle.test")

    record = engine.audit_query(
        adapter_id="adp.kalshi",
        query={
            "query_id": "q-001",
            "market_type": "prediction_market",
            "symbol": "KXTEST",
        },
        resolver_output={
            "query_id": "q-001",
            "resolved": True,
            "markets": [{"universal_market_id": "umm.test.001"}],
        },
        market_model={
            "schema_version": "1.0",
            "universal_market_id": "umm.test.001",
            "market_type": "prediction_market",
        },
        telemetry={"latency_ms": 12},
    )

    assert record.passed is True
    assert record.adapter_id == "adp.kalshi"
    assert record.query_id == "q-001"
    assert len(record.query_hash) == 64
    assert len(record.resolver_hash) == 64
    assert len(record.market_model_hash) == 64
    assert len(record.replay_key) == 64
    assert record.read_only_guardrails["oracle_read_only"] is True
    assert record.read_only_guardrails["execution_owner"] == "Q_SERIES_ONLY"

    bad = engine.audit_query(
        adapter_id="adp.bad",
        query={"query_id": "q-002", "market_type": "prediction_market"},
        resolver_output={"query_id": "q-002", "executed": True, "order_submitted": True},
        market_model={"market_id": "m-1"},
    )

    assert bad.passed is False
    assert any(f.code == "EXECUTION_BOUNDARY_VIOLATION" for f in bad.findings)

    snapshot = engine.telemetry_snapshot()
    assert snapshot["records"] == 2
    assert snapshot["passed"] == 1
    assert snapshot["failed"] == 1
    assert snapshot["read_only_guardrails"] == READ_ONLY_GUARDRAILS

    manifest = engine.replay_manifest()
    assert manifest["record_count"] == 2
    assert manifest["records"][0]["query_hash"] == record.query_hash

    batch = engine.audit_many([
        {
            "adapter_id": "adp.batch",
            "query": {"query_id": "q-003", "market": "generic"},
            "resolver_output": {"result": {"ok": True}},
            "market_model": {"schema_version": "1.0", "market_type": "generic"},
        }
    ])
    assert len(batch) == 1
    assert batch[0].query_id == "q-003"


if __name__ == "__main__":
    test_oi_185_query_audit_engine()
    print("[PASS] OI-185 Universal Market Adapter Query Audit Engine")
'''.lstrip(), encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

import_line = "from .universal_market_adapter_query_audit_engine import UniversalMarketAdapterQueryAuditEngine, create_query_audit_engine\n"
if import_line not in init_text:
    init_text += ("\n" if init_text and not init_text.endswith("\n") else "") + import_line
INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-185 INSTALLER")
print(" Universal Market Adapter Query Audit Engine")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-185 installed")
print()
print("Run:")
print("py test_oi_185_universal_market_adapter_query_audit_engine.py")