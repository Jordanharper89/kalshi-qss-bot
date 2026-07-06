"""
OI-168 — Oracle Universal Market Adapter Telemetry Engine

Read-only telemetry engine for Universal Market Adapter validation output.

Purpose:
- Collect adapter validation telemetry across Universal Market Model packets.
- Track packet counts, validation status, latency, issue rates, adapter health,
  domain coverage, replayability, explainability, and safety contract adherence.
- Provide institutional telemetry summaries without execution capability.

Oracle never executes trades, manages positions, or submits orders.
Execution ownership remains with Q Series.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List


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
class AdapterTelemetryRecord:
    telemetry_record_id: str
    adapter_id: str
    domain: str
    validation_status: str
    record_count: int
    issue_count: int
    critical_count: int
    warning_count: int
    health_score: float
    health_status: str
    lineage_hash: str
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"


@dataclass
class OracleUniversalMarketAdapterTelemetryEngine:
    name: str = "oracle_universal_market_adapter_telemetry_engine"
    version: str = "OI-168"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    telemetry_schema_version: str = "universal_market_adapter_telemetry_v1"

    def classify_health(self, score: float) -> str:
        if score >= 95:
            return "institutional_adapter_health"
        if score >= 85:
            return "healthy_adapter"
        if score >= 70:
            return "adapter_health_watch"
        if score >= 50:
            return "adapter_degraded"
        return "adapter_unhealthy"

    def score_validation(self, report: Dict[str, Any]) -> float:
        report = _safe_dict(report)

        score = 100.0

        if report.get("validation_status") == "adapter_packet_invalid":
            score -= 45
        elif report.get("validation_status") == "adapter_packet_valid_with_warnings":
            score -= 12
        elif report.get("validation_status") != "adapter_packet_valid":
            score -= 25

        score -= min(_num(report.get("critical_count")) * 15, 45)
        score -= min(_num(report.get("warning_count")) * 4, 20)

        if report.get("read_only") is not True:
            score -= 25
        if report.get("execution_allowed") is not False:
            score -= 35
        if report.get("execution_owner") != "Q Series":
            score -= 20

        return round(max(0.0, min(100.0, score)), 2)

    def build_record(self, validation_report: Dict[str, Any]) -> AdapterTelemetryRecord:
        report = _safe_dict(validation_report)

        adapter_id = str(report.get("adapter_id") or "unknown_adapter")
        domain = str(report.get("domain") or "UNKNOWN").upper()
        validation_status = str(report.get("validation_status") or "unknown_validation_status")
        record_count = int(_num(report.get("record_count"), 0))
        issue_count = int(_num(report.get("issue_count"), 0))
        critical_count = int(_num(report.get("critical_count"), 0))
        warning_count = int(_num(report.get("warning_count"), 0))
        health_score = self.score_validation(report)

        payload = {
            "adapter_id": adapter_id,
            "domain": domain,
            "validation_status": validation_status,
            "record_count": record_count,
            "issue_count": issue_count,
            "critical_count": critical_count,
            "warning_count": warning_count,
            "health_score": health_score,
            "source_validation_id": report.get("adapter_validation_id"),
        }

        lineage_hash = _hash(payload)

        return AdapterTelemetryRecord(
            telemetry_record_id=_hash({"payload": payload, "lineage": lineage_hash}),
            adapter_id=adapter_id,
            domain=domain,
            validation_status=validation_status,
            record_count=record_count,
            issue_count=issue_count,
            critical_count=critical_count,
            warning_count=warning_count,
            health_score=health_score,
            health_status=self.classify_health(health_score),
            lineage_hash=lineage_hash,
            read_only=True,
            execution_allowed=False,
            execution_owner=self.execution_owner,
        )

    def collect(self, validation_reports: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        records = [self.build_record(report) for report in validation_reports]
        records.sort(key=lambda r: (r.domain, r.adapter_id))

        adapter_counts: Dict[str, int] = {}
        domain_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}
        health_counts: Dict[str, int] = {}

        total_health = 0.0
        total_records = 0
        total_issues = 0
        total_critical = 0
        total_warnings = 0

        for record in records:
            adapter_counts[record.adapter_id] = adapter_counts.get(record.adapter_id, 0) + 1
            domain_counts[record.domain] = domain_counts.get(record.domain, 0) + 1
            status_counts[record.validation_status] = status_counts.get(record.validation_status, 0) + 1
            health_counts[record.health_status] = health_counts.get(record.health_status, 0) + 1
            total_health += record.health_score
            total_records += record.record_count
            total_issues += record.issue_count
            total_critical += record.critical_count
            total_warnings += record.warning_count

        average_health = round(total_health / len(records), 2) if records else 0.0

        if not records:
            telemetry_status = "empty_adapter_telemetry"
        elif total_critical:
            telemetry_status = "adapter_telemetry_critical"
        elif total_warnings:
            telemetry_status = "adapter_telemetry_warnings"
        elif average_health >= 95:
            telemetry_status = "adapter_telemetry_institutional"
        else:
            telemetry_status = "adapter_telemetry_healthy"

        telemetry_id = _hash({
            "records": [record.__dict__ for record in records],
            "status": telemetry_status,
            "average_health": average_health,
        })

        return {
            "module": self.name,
            "version": self.version,
            "telemetry_schema_version": self.telemetry_schema_version,
            "adapter_telemetry_id": telemetry_id,
            "telemetry_status": telemetry_status,
            "collected_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "adapter_count": len(adapter_counts),
            "domain_count": len(domain_counts),
            "telemetry_record_count": len(records),
            "total_output_records": total_records,
            "total_issue_count": total_issues,
            "total_critical_count": total_critical,
            "total_warning_count": total_warnings,
            "average_health_score": average_health,
            "adapter_counts": adapter_counts,
            "domain_counts": domain_counts,
            "validation_status_counts": status_counts,
            "health_status_counts": health_counts,
            "executive_summary": {
                "headline": (
                    "Universal Market adapter telemetry is institutional."
                    if telemetry_status == "adapter_telemetry_institutional"
                    else f"Universal Market adapter telemetry status: {telemetry_status}."
                ),
                "adapter_telemetry_id": telemetry_id,
                "adapter_count": len(adapter_counts),
                "domain_count": len(domain_counts),
                "average_health_score": average_health,
                "operator_note": "Adapter telemetry is read-only. Q Series owns execution.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "records": [record.__dict__ for record in records],
        }

    def adapter_health(self, telemetry: Dict[str, Any], adapter_id: str) -> Dict[str, Any]:
        telemetry = _safe_dict(telemetry)
        records = _safe_list(telemetry.get("records"))
        target = str(adapter_id or "").strip().lower()

        matches = [
            _safe_dict(record)
            for record in records
            if str(_safe_dict(record).get("adapter_id") or "").strip().lower() == target
        ]

        if not matches:
            return {
                "module": self.name,
                "version": self.version,
                "found": False,
                "adapter_id": adapter_id,
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
                "records": [],
            }

        avg = round(sum(_num(record.get("health_score")) for record in matches) / len(matches), 2)

        return {
            "module": self.name,
            "version": self.version,
            "found": True,
            "adapter_id": adapter_id,
            "average_health_score": avg,
            "health_status": self.classify_health(avg),
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
            "records": matches,
        }


oracle_universal_market_adapter_telemetry_engine = OracleUniversalMarketAdapterTelemetryEngine()
