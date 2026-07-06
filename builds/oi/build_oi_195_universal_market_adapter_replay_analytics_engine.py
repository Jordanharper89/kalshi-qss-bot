from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "universal_market_adapter_replay_analytics_engine.py"
TEST = ROOT / "test_oi_195_universal_market_adapter_replay_analytics_engine.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
"""
OI-195 — Oracle Universal Market Adapter Replay Analytics Engine

Read-only analytics layer for replay registry/search/filter/query artifacts.

This engine analyzes replay artifacts without executing trades, routing orders,
submitting orders, managing positions, or mutating market state. Oracle remains
intelligence-only. Q Series remains the only execution engine.
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


def _safe_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return [value]


@dataclass(frozen=True)
class ReplayAnalyticsFinding:
    code: str
    severity: str
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayAnalyticsBucket:
    name: str
    count: int
    percentage: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayAnalyticsReport:
    analytics_id: str
    created_at: str
    oracle_instance_id: str
    module_id: str
    module_name: str
    artifact_count: int
    certified_count: int
    rejected_count: int
    passed_count: int
    failed_count: int
    adapter_count: int
    manifest_count: int
    certification_count: int
    validation_count: int
    analytics_hash: str
    read_only_guardrails: Dict[str, Any]
    status_buckets: List[ReplayAnalyticsBucket]
    adapter_buckets: List[ReplayAnalyticsBucket]
    certification_level_buckets: List[ReplayAnalyticsBucket]
    findings: List[ReplayAnalyticsFinding]
    telemetry: Dict[str, Any]
    explainability: Dict[str, Any]

    @property
    def passed(self) -> bool:
        return not any(f.severity in {"critical", "error"} for f in self.findings)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["passed"] = self.passed
        return data


class UniversalMarketAdapterReplayAnalyticsEngine:
    """
    Produces institutional analytics over replay artifacts.

    Canonical input is any replay record-like object from OI-190/OI-191/OI-192/OI-193/OI-194
    that exposes to_dict(), __dict__, or mapping fields.
    """

    module_id = "OI-195"
    module_name = "Oracle Universal Market Adapter Replay Analytics Engine"

    def __init__(self, oracle_instance_id: str = "oracle.default") -> None:
        self.oracle_instance_id = oracle_instance_id
        self._reports: List[ReplayAnalyticsReport] = []

    def analyze(self, artifacts: Iterable[Any], *, analytics_context: Optional[Mapping[str, Any]] = None) -> ReplayAnalyticsReport:
        context = _safe_dict(analytics_context)
        normalized = [self._normalize_artifact(item) for item in artifacts]
        findings = self._evaluate(normalized, context)

        artifact_count = len(normalized)
        certified_count = sum(1 for item in normalized if item.get("certified") is True)
        rejected_count = sum(1 for item in normalized if str(item.get("status", "")).lower() in {"rejected", "not_certified", "failed"})
        passed_count = sum(1 for item in normalized if item.get("passed") is True)
        failed_count = sum(1 for item in normalized if item.get("passed") is False)
        adapter_count = len({item.get("adapter_id") for item in normalized if item.get("adapter_id")})
        manifest_count = len({item.get("manifest_id") for item in normalized if item.get("manifest_id")})
        certification_count = len({item.get("certification_id") for item in normalized if item.get("certification_id")})
        validation_count = len({item.get("validation_id") for item in normalized if item.get("validation_id")})

        status_buckets = self._bucketize(normalized, "status")
        adapter_buckets = self._bucketize(normalized, "adapter_id")
        certification_level_buckets = self._bucketize(normalized, "certification_level")

        payload = {
            "oracle_instance_id": self.oracle_instance_id,
            "module_id": self.module_id,
            "artifact_count": artifact_count,
            "certified_count": certified_count,
            "rejected_count": rejected_count,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "adapter_count": adapter_count,
            "manifest_count": manifest_count,
            "certification_count": certification_count,
            "validation_count": validation_count,
            "status_buckets": [bucket.to_dict() for bucket in status_buckets],
            "adapter_buckets": [bucket.to_dict() for bucket in adapter_buckets],
            "certification_level_buckets": [bucket.to_dict() for bucket in certification_level_buckets],
            "findings": [finding.to_dict() for finding in findings],
            "context": context,
        }
        analytics_hash = _hash(payload)

        report = ReplayAnalyticsReport(
            analytics_id="oi195.analytics." + analytics_hash[:24],
            created_at=_utc_now(),
            oracle_instance_id=self.oracle_instance_id,
            module_id=self.module_id,
            module_name=self.module_name,
            artifact_count=artifact_count,
            certified_count=certified_count,
            rejected_count=rejected_count,
            passed_count=passed_count,
            failed_count=failed_count,
            adapter_count=adapter_count,
            manifest_count=manifest_count,
            certification_count=certification_count,
            validation_count=validation_count,
            analytics_hash=analytics_hash,
            read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
            status_buckets=status_buckets,
            adapter_buckets=adapter_buckets,
            certification_level_buckets=certification_level_buckets,
            findings=findings,
            telemetry={
                "module_id": self.module_id,
                "module_name": self.module_name,
                "oracle_instance_id": self.oracle_instance_id,
                "artifact_count": artifact_count,
                "certified_count": certified_count,
                "rejected_count": rejected_count,
                "passed_count": passed_count,
                "failed_count": failed_count,
                "adapter_count": adapter_count,
                "manifest_count": manifest_count,
                "certification_count": certification_count,
                "validation_count": validation_count,
                "finding_count": len(findings),
                "context_hash": _hash(context),
            },
            explainability={
                "purpose": "Analyze replay artifacts for institutional telemetry and replay health without execution authority.",
                "read_only_reason": "Analytics inspects replay metadata only and cannot execute, route, submit, or manage positions.",
                "execution_boundary": "Q Series remains the only execution engine.",
                "canonical_inputs": [
                    "OI-190 replay registry records",
                    "OI-191 lookup records",
                    "OI-192 search results",
                    "OI-193 filtered replay results",
                    "OI-194 replay query results",
                ],
                "analytics_dimensions": [
                    "certification status",
                    "pass/fail status",
                    "adapter coverage",
                    "manifest coverage",
                    "certification coverage",
                    "validation coverage",
                    "certification level distribution",
                ],
            },
        )
        self._reports.append(report)
        return report

    def summarize(self, artifacts: Iterable[Any]) -> Dict[str, Any]:
        report = self.analyze(artifacts)
        return {
            "analytics_id": report.analytics_id,
            "artifact_count": report.artifact_count,
            "certified_count": report.certified_count,
            "rejected_count": report.rejected_count,
            "passed_count": report.passed_count,
            "failed_count": report.failed_count,
            "adapter_count": report.adapter_count,
            "manifest_count": report.manifest_count,
            "certification_count": report.certification_count,
            "validation_count": report.validation_count,
            "passed": report.passed,
            "analytics_hash": report.analytics_hash,
        }

    def reports(self) -> List[ReplayAnalyticsReport]:
        return list(self._reports)

    def latest_report(self) -> Optional[ReplayAnalyticsReport]:
        return self._reports[-1] if self._reports else None

    def telemetry_snapshot(self) -> Dict[str, Any]:
        latest = self.latest_report()
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "oracle_instance_id": self.oracle_instance_id,
            "report_count": len(self._reports),
            "latest_analytics_id": latest.analytics_id if latest else None,
            "latest_analytics_hash": latest.analytics_hash if latest else None,
            "latest_artifact_count": latest.artifact_count if latest else 0,
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
        }

    def _normalize_artifact(self, artifact: Any) -> Dict[str, Any]:
        data = _safe_dict(artifact)
        telemetry = _safe_dict(data.get("telemetry"))
        explainability = _safe_dict(data.get("explainability"))

        status = str(data.get("status") or telemetry.get("status") or "unknown").lower()
        certified = data.get("certified")
        if certified is None:
            certified = status in {"certified", "registered", "ok", "passed"}

        passed = data.get("passed")
        if passed is None:
            passed = bool(certified)

        return {
            "registration_id": data.get("registration_id") or data.get("registry_id") or data.get("id"),
            "registry_id": data.get("registry_id"),
            "certification_id": data.get("certification_id") or telemetry.get("certification_id"),
            "validation_id": data.get("validation_id") or telemetry.get("validation_id"),
            "manifest_id": data.get("manifest_id") or telemetry.get("manifest_id"),
            "adapter_id": data.get("adapter_id") or telemetry.get("adapter_id"),
            "market_type": data.get("market_type") or telemetry.get("market_type"),
            "symbol": data.get("symbol") or telemetry.get("symbol"),
            "status": status,
            "certified": bool(certified),
            "passed": bool(passed),
            "certification_level": data.get("certification_level") or telemetry.get("certification_level") or ("certified" if certified else "not_certified"),
            "certification_hash": data.get("certification_hash"),
            "manifest_hash": data.get("manifest_hash"),
            "chain_hash": data.get("chain_hash"),
            "registry_hash": data.get("registry_hash"),
            "telemetry": telemetry,
            "explainability": explainability,
            "raw_hash": _hash(data),
        }

    def _bucketize(self, artifacts: List[Dict[str, Any]], field_name: str) -> List[ReplayAnalyticsBucket]:
        total = len(artifacts)
        counts: Dict[str, int] = {}
        for item in artifacts:
            value = item.get(field_name)
            if value in (None, ""):
                value = "unknown"
            value = str(value)
            counts[value] = counts.get(value, 0) + 1

        buckets: List[ReplayAnalyticsBucket] = []
        for name, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])):
            pct = round((count / total) * 100.0, 4) if total else 0.0
            buckets.append(ReplayAnalyticsBucket(name=name, count=count, percentage=pct))
        return buckets

    def _evaluate(self, artifacts: List[Dict[str, Any]], context: Dict[str, Any]) -> List[ReplayAnalyticsFinding]:
        findings: List[ReplayAnalyticsFinding] = []

        if not artifacts:
            findings.append(ReplayAnalyticsFinding(
                code="NO_REPLAY_ARTIFACTS",
                severity="warning",
                message="No replay artifacts were supplied for analytics.",
            ))
            return findings

        missing_manifest = [item.get("registration_id") or item.get("raw_hash") for item in artifacts if not item.get("manifest_id")]
        if missing_manifest:
            findings.append(ReplayAnalyticsFinding(
                code="MANIFEST_LINKAGE_INCOMPLETE",
                severity="warning",
                message="Some replay artifacts are missing manifest identifiers.",
                evidence={"items": missing_manifest[:25], "count": len(missing_manifest)},
            ))

        missing_certification = [item.get("registration_id") or item.get("raw_hash") for item in artifacts if not item.get("certification_id")]
        if missing_certification:
            findings.append(ReplayAnalyticsFinding(
                code="CERTIFICATION_LINKAGE_INCOMPLETE",
                severity="warning",
                message="Some replay artifacts are missing certification identifiers.",
                evidence={"items": missing_certification[:25], "count": len(missing_certification)},
            ))

        rejected = [item.get("registration_id") or item.get("raw_hash") for item in artifacts if item.get("certified") is False]
        if rejected:
            findings.append(ReplayAnalyticsFinding(
                code="REJECTED_REPLAY_ARTIFACTS_PRESENT",
                severity="info",
                message="Analytics set contains replay artifacts that are not certified.",
                evidence={"items": rejected[:25], "count": len(rejected)},
            ))

        context_text = _stable_json(context).lower()
        detected_execution_terms = [term for term in ["execute", "submit_order", "route_order", "trade", "position"] if term in context_text]
        if detected_execution_terms:
            findings.append(ReplayAnalyticsFinding(
                code="EXECUTION_LANGUAGE_IN_ANALYTICS_CONTEXT",
                severity="warning",
                message="Analytics context contains execution-like language. Oracle analytics remains read-only.",
                evidence={"detected_terms": detected_execution_terms},
            ))

        return findings


def create_replay_analytics_engine(oracle_instance_id: str = "oracle.default") -> UniversalMarketAdapterReplayAnalyticsEngine:
    return UniversalMarketAdapterReplayAnalyticsEngine(oracle_instance_id=oracle_instance_id)


__all__ = [
    "READ_ONLY_GUARDRAILS",
    "ReplayAnalyticsFinding",
    "ReplayAnalyticsBucket",
    "ReplayAnalyticsReport",
    "UniversalMarketAdapterReplayAnalyticsEngine",
    "create_replay_analytics_engine",
]
'''.lstrip(), encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_replay_analytics_engine import (
    READ_ONLY_GUARDRAILS,
    ReplayAnalyticsReport,
    UniversalMarketAdapterReplayAnalyticsEngine,
    create_replay_analytics_engine,
)


class ObjectRecord:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def to_dict(self):
        return dict(self.__dict__)


def test_oi_195_universal_market_adapter_replay_analytics_engine():
    engine = create_replay_analytics_engine("oracle.test")

    artifacts = [
        {
            "registration_id": "reg-001",
            "certification_id": "cert-001",
            "validation_id": "val-001",
            "manifest_id": "man-001",
            "adapter_id": "adp.kalshi",
            "symbol": "KXTEST",
            "market_type": "prediction_market",
            "status": "registered",
            "certified": True,
            "passed": True,
            "certification_level": "certified",
            "certification_hash": "a" * 64,
            "manifest_hash": "b" * 64,
            "chain_hash": "c" * 64,
            "registry_hash": "d" * 64,
        },
        ObjectRecord(
            registration_id="reg-002",
            certification_id="cert-002",
            validation_id="val-002",
            manifest_id="man-002",
            adapter_id="adp.kalshi",
            symbol="KXTEST2",
            market_type="prediction_market",
            status="registered",
            certified=True,
            passed=True,
            certification_level="certified_with_warnings",
            certification_hash="e" * 64,
            manifest_hash="f" * 64,
            chain_hash="g" * 64,
            registry_hash="h" * 64,
        ),
        {
            "registration_id": "reg-003",
            "certification_id": "cert-003",
            "validation_id": "val-003",
            "manifest_id": "man-003",
            "adapter_id": "adp.polymarket",
            "symbol": "PMTEST",
            "market_type": "prediction_market",
            "status": "rejected",
            "certified": False,
            "passed": False,
            "certification_level": "not_certified",
        },
    ]

    report = engine.analyze(artifacts, analytics_context={"gate": "unit", "scope": "replay_analytics"})

    assert isinstance(report, ReplayAnalyticsReport)
    assert report.module_id == "OI-195"
    assert report.artifact_count == 3
    assert report.certified_count == 2
    assert report.rejected_count == 1
    assert report.passed_count == 2
    assert report.failed_count == 1
    assert report.adapter_count == 2
    assert report.manifest_count == 3
    assert report.certification_count == 3
    assert report.validation_count == 3
    assert len(report.analytics_hash) == 64
    assert report.read_only_guardrails == READ_ONLY_GUARDRAILS
    assert report.passed is True

    status = {bucket.name: bucket.count for bucket in report.status_buckets}
    assert status["registered"] == 2
    assert status["rejected"] == 1

    adapters = {bucket.name: bucket.count for bucket in report.adapter_buckets}
    assert adapters["adp.kalshi"] == 2
    assert adapters["adp.polymarket"] == 1

    levels = {bucket.name: bucket.count for bucket in report.certification_level_buckets}
    assert levels["certified"] == 1
    assert levels["certified_with_warnings"] == 1
    assert levels["not_certified"] == 1

    summary = engine.summarize(artifacts)
    assert summary["artifact_count"] == 3
    assert summary["certified_count"] == 2
    assert summary["adapter_count"] == 2
    assert summary["passed"] is True

    snapshot = engine.telemetry_snapshot()
    assert snapshot["module_id"] == "OI-195"
    assert snapshot["report_count"] == 2
    assert snapshot["latest_artifact_count"] == 3
    assert snapshot["read_only_guardrails"] == READ_ONLY_GUARDRAILS

    empty_report = engine.analyze([])
    assert empty_report.artifact_count == 0
    assert empty_report.passed is True
    assert any(f.code == "NO_REPLAY_ARTIFACTS" for f in empty_report.findings)

    context_report = engine.analyze(artifacts, analytics_context={"note": "do not execute trades"})
    assert any(f.code == "EXECUTION_LANGUAGE_IN_ANALYTICS_CONTEXT" for f in context_report.findings)

    direct = UniversalMarketAdapterReplayAnalyticsEngine("oracle.direct")
    assert direct.telemetry_snapshot()["report_count"] == 0


if __name__ == "__main__":
    test_oi_195_universal_market_adapter_replay_analytics_engine()
    print("[PASS] OI-195 Universal Market Adapter Replay Analytics Engine")
'''.lstrip(), encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

import_line = "from .universal_market_adapter_replay_analytics_engine import UniversalMarketAdapterReplayAnalyticsEngine, create_replay_analytics_engine\n"
if import_line not in init_text:
    init_text += ("\n" if init_text and not init_text.endswith("\n") else "") + import_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-195 INSTALLER")
print(" Universal Market Adapter Replay Analytics Engine")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-195 installed")
print()
print("Run:")
print("py test_oi_195_universal_market_adapter_replay_analytics_engine.py")
