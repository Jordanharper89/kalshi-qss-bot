"""
OI-167 — Oracle Universal Market Adapter Validation Engine

Read-only validation engine for Universal Market Adapter output.

Purpose:
- Validate adapter output packets before Oracle Intelligence consumes them.
- Confirm adapter output maps into the Universal Market Model.
- Enforce lineage, timestamp, source, confidence, telemetry, replayability,
  explainability, and read-only execution boundaries.

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
class AdapterValidationIssue:
    adapter_id: str
    record_id: str
    severity: str
    code: str
    message: str


@dataclass
class OracleUniversalMarketAdapterValidationEngine:
    name: str = "oracle_universal_market_adapter_validation_engine"
    version: str = "OI-167"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    validation_schema_version: str = "universal_market_adapter_validation_v1"

    required_packet_fields = [
        "adapter_id",
        "domain",
        "records",
        "read_only",
        "execution_allowed",
        "execution_owner",
    ]

    required_record_fields = [
        "domain",
        "symbol",
        "timestamp",
        "source",
        "price",
        "confidence",
        "lineage",
        "read_only",
        "execution_allowed",
        "execution_owner",
    ]

    supported_domains = [
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
    ]

    def _validate_packet_contract(self, packet: Dict[str, Any]) -> List[AdapterValidationIssue]:
        packet = _safe_dict(packet)
        adapter_id = str(packet.get("adapter_id") or "unknown_adapter")
        issues: List[AdapterValidationIssue] = []

        for field in self.required_packet_fields:
            if packet.get(field) in (None, ""):
                issues.append(AdapterValidationIssue(
                    adapter_id=adapter_id,
                    record_id="packet",
                    severity="critical",
                    code="missing_packet_field",
                    message=f"Adapter packet missing required field: {field}",
                ))

        if packet.get("read_only") is not True:
            issues.append(AdapterValidationIssue(
                adapter_id=adapter_id,
                record_id="packet",
                severity="critical",
                code="packet_read_only_violation",
                message="Adapter packet must be read_only=True.",
            ))

        if packet.get("execution_allowed") is not False:
            issues.append(AdapterValidationIssue(
                adapter_id=adapter_id,
                record_id="packet",
                severity="critical",
                code="packet_execution_violation",
                message="Adapter packet must not allow execution.",
            ))

        if packet.get("execution_owner") != "Q Series":
            issues.append(AdapterValidationIssue(
                adapter_id=adapter_id,
                record_id="packet",
                severity="critical",
                code="packet_execution_owner_violation",
                message="Adapter packet execution_owner must be Q Series.",
            ))

        if str(packet.get("domain") or "").upper() not in self.supported_domains:
            issues.append(AdapterValidationIssue(
                adapter_id=adapter_id,
                record_id="packet",
                severity="warning",
                code="unsupported_packet_domain",
                message=f"Adapter packet domain {packet.get('domain')} is not supported.",
            ))

        records = packet.get("records")
        if not isinstance(records, list):
            issues.append(AdapterValidationIssue(
                adapter_id=adapter_id,
                record_id="packet",
                severity="critical",
                code="records_not_list",
                message="Adapter packet records must be a list.",
            ))

        return issues

    def _validate_record(self, packet: Dict[str, Any], record: Dict[str, Any], index: int) -> List[AdapterValidationIssue]:
        packet = _safe_dict(packet)
        record = _safe_dict(record)

        adapter_id = str(packet.get("adapter_id") or record.get("adapter_id") or "unknown_adapter")
        record_id = str(record.get("umm_record_id") or record.get("record_id") or f"record-{index}")
        issues: List[AdapterValidationIssue] = []

        for field in self.required_record_fields:
            if record.get(field) in (None, ""):
                issues.append(AdapterValidationIssue(
                    adapter_id=adapter_id,
                    record_id=record_id,
                    severity="critical",
                    code="missing_record_field",
                    message=f"Adapter output record missing required UMM field: {field}",
                ))

        packet_domain = str(packet.get("domain") or "").upper()
        record_domain = str(record.get("domain") or "").upper()

        if record_domain and packet_domain and record_domain != packet_domain:
            issues.append(AdapterValidationIssue(
                adapter_id=adapter_id,
                record_id=record_id,
                severity="critical",
                code="domain_mismatch",
                message="Record domain does not match adapter packet domain.",
            ))

        if record.get("read_only") is not True:
            issues.append(AdapterValidationIssue(
                adapter_id=adapter_id,
                record_id=record_id,
                severity="critical",
                code="record_read_only_violation",
                message="Adapter output record must be read_only=True.",
            ))

        if record.get("execution_allowed") is not False:
            issues.append(AdapterValidationIssue(
                adapter_id=adapter_id,
                record_id=record_id,
                severity="critical",
                code="record_execution_violation",
                message="Adapter output record must not allow execution.",
            ))

        if record.get("execution_owner") != "Q Series":
            issues.append(AdapterValidationIssue(
                adapter_id=adapter_id,
                record_id=record_id,
                severity="critical",
                code="record_execution_owner_violation",
                message="Adapter output record execution_owner must be Q Series.",
            ))

        confidence = _num(record.get("confidence"), -1)
        if confidence < 0 or confidence > 100:
            issues.append(AdapterValidationIssue(
                adapter_id=adapter_id,
                record_id=record_id,
                severity="critical",
                code="confidence_out_of_bounds",
                message="Adapter output record confidence must be between 0 and 100.",
            ))

        if not str(record.get("lineage") or "").strip():
            issues.append(AdapterValidationIssue(
                adapter_id=adapter_id,
                record_id=record_id,
                severity="critical",
                code="missing_lineage",
                message="Adapter output record missing lineage.",
            ))

        if not str(record.get("timestamp") or "").strip():
            issues.append(AdapterValidationIssue(
                adapter_id=adapter_id,
                record_id=record_id,
                severity="critical",
                code="missing_timestamp",
                message="Adapter output record missing timestamp.",
            ))

        telemetry = record.get("telemetry")
        if telemetry is not None and not isinstance(telemetry, dict):
            issues.append(AdapterValidationIssue(
                adapter_id=adapter_id,
                record_id=record_id,
                severity="warning",
                code="telemetry_not_dict",
                message="Telemetry should be a dictionary when provided.",
            ))

        return issues

    def validate_packet(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        packet = _safe_dict(packet)
        records = _safe_list(packet.get("records"))
        issues: List[AdapterValidationIssue] = []

        issues.extend(self._validate_packet_contract(packet))

        if isinstance(packet.get("records"), list):
            for index, record in enumerate(records, start=1):
                issues.extend(self._validate_record(packet, _safe_dict(record), index))

        critical_count = sum(1 for issue in issues if issue.severity == "critical")
        warning_count = sum(1 for issue in issues if issue.severity == "warning")

        if critical_count:
            validation_status = "adapter_packet_invalid"
        elif warning_count:
            validation_status = "adapter_packet_valid_with_warnings"
        else:
            validation_status = "adapter_packet_valid"

        validation_id = _hash({
            "adapter_id": packet.get("adapter_id"),
            "domain": packet.get("domain"),
            "record_count": len(records),
            "issues": [issue.__dict__ for issue in issues],
            "status": validation_status,
        })

        return {
            "module": self.name,
            "version": self.version,
            "validation_schema_version": self.validation_schema_version,
            "adapter_validation_id": validation_id,
            "validation_status": validation_status,
            "validated_at": _utc_now(),
            "adapter_id": packet.get("adapter_id"),
            "domain": str(packet.get("domain") or "UNKNOWN").upper(),
            "record_count": len(records),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "issue_count": len(issues),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "executive_summary": {
                "headline": (
                    "Universal Market adapter packet validated."
                    if validation_status == "adapter_packet_valid"
                    else f"Universal Market adapter packet status: {validation_status}."
                ),
                "adapter_validation_id": validation_id,
                "adapter_id": packet.get("adapter_id"),
                "domain": str(packet.get("domain") or "UNKNOWN").upper(),
                "record_count": len(records),
                "issue_count": len(issues),
                "operator_note": "Adapter output is ingestion-only. Oracle remains read-only. Q Series owns execution.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "issues": [issue.__dict__ for issue in issues],
        }

    def validate_batch(self, packets: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        reports = [self.validate_packet(packet) for packet in packets]

        invalid_count = sum(1 for report in reports if report["validation_status"] == "adapter_packet_invalid")
        warning_count = sum(1 for report in reports if report["validation_status"] == "adapter_packet_valid_with_warnings")
        valid_count = sum(1 for report in reports if report["validation_status"] == "adapter_packet_valid")

        if invalid_count:
            batch_status = "adapter_validation_batch_invalid"
        elif warning_count:
            batch_status = "adapter_validation_batch_valid_with_warnings"
        else:
            batch_status = "adapter_validation_batch_valid"

        batch_id = _hash({
            "reports": reports,
            "batch_status": batch_status,
        })

        return {
            "module": self.name,
            "version": self.version,
            "validation_schema_version": self.validation_schema_version,
            "adapter_validation_batch_id": batch_id,
            "batch_status": batch_status,
            "validated_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "packet_count": len(reports),
            "valid_count": valid_count,
            "warning_count": warning_count,
            "invalid_count": invalid_count,
            "reports": reports,
        }


oracle_universal_market_adapter_validation_engine = OracleUniversalMarketAdapterValidationEngine()
