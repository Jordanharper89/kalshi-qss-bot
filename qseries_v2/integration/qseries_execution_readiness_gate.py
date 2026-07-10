"""
INT-014 Q Series Execution Readiness Gate

Performs Q Series-owned risk and execution-readiness review for valid INT-013
execution-intake proposals. This module never places orders, calls exchanges,
moves funds, or mutates portfolios.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Dict, Iterable, Mapping, Tuple

from qseries_v2.integration.qseries_execution_intake_record import (
    QSeriesExecutionIntakeResult,
)


SCHEMA_VERSION = "INT-014"
ENGINE_ID = "INT-014"
READ_ONLY = True
EXECUTION_ALLOWED = False
QSERIES_OWNED = True
FINAL_EXECUTION_GATE_REQUIRED = True


class ExecutionReadinessStatus(str, Enum):
    READY_FOR_EXECUTION_GATE = "ready_for_execution_gate"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ExecutionReadinessLimits:
    max_records: int = 25
    require_unique_markets: bool = True
    require_intake_gate: bool = True
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExecutionReadinessRecord:
    readiness_id: str
    source_intake_id: str
    opportunity_id: str
    fingerprint: str
    market_id: str
    venue_id: str
    direction: str
    status: ExecutionReadinessStatus
    reasons: Tuple[str, ...]
    source_intake_hash: str
    readiness_hash: str
    observed_at: str
    read_only: bool = READ_ONLY
    execution_allowed: bool = EXECUTION_ALLOWED
    qseries_owned: bool = QSERIES_OWNED
    final_execution_gate_required: bool = FINAL_EXECUTION_GATE_REQUIRED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "readiness_id": self.readiness_id,
            "source_intake_id": self.source_intake_id,
            "opportunity_id": self.opportunity_id,
            "fingerprint": self.fingerprint,
            "market_id": self.market_id,
            "venue_id": self.venue_id,
            "direction": self.direction,
            "status": self.status.value,
            "reasons": list(self.reasons),
            "source_intake_hash": self.source_intake_hash,
            "readiness_hash": self.readiness_hash,
            "observed_at": self.observed_at,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "qseries_owned": self.qseries_owned,
            "final_execution_gate_required": self.final_execution_gate_required,
        }


@dataclass(frozen=True)
class ExecutionReadinessCheck:
    check_id: str
    passed: bool
    explanation: str
    details: Tuple[Tuple[str, Any], ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "passed": self.passed,
            "explanation": self.explanation,
            "details": _metadata_dict(self.details),
        }


@dataclass(frozen=True)
class QSeriesExecutionReadinessResult:
    schema_version: str
    engine_id: str
    observed_at: str
    status: str
    ready_records: Tuple[ExecutionReadinessRecord, ...]
    rejected_records: Tuple[ExecutionReadinessRecord, ...]
    checks: Tuple[ExecutionReadinessCheck, ...]
    pass_count: int
    fail_count: int
    ready_count: int
    rejected_count: int
    readiness_hash: str
    read_only: bool
    execution_allowed: bool
    qseries_owned: bool
    final_execution_gate_required: bool
    explanation: str
    telemetry: Tuple[Tuple[str, Any], ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return self.fail_count == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "observed_at": self.observed_at,
            "status": self.status,
            "ready_records": [record.to_dict() for record in self.ready_records],
            "rejected_records": [record.to_dict() for record in self.rejected_records],
            "checks": [check.to_dict() for check in self.checks],
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "ready_count": self.ready_count,
            "rejected_count": self.rejected_count,
            "readiness_hash": self.readiness_hash,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "qseries_owned": self.qseries_owned,
            "final_execution_gate_required": self.final_execution_gate_required,
            "explanation": self.explanation,
            "telemetry": _metadata_dict(self.telemetry),
            "passed": self.passed,
        }

    def verify_readiness_hash(self) -> bool:
        return self.readiness_hash == _result_hash(
            observed_at=self.observed_at,
            status=self.status,
            ready_records=self.ready_records,
            rejected_records=self.rejected_records,
            checks=self.checks,
            pass_count=self.pass_count,
            fail_count=self.fail_count,
            ready_count=self.ready_count,
            rejected_count=self.rejected_count,
            telemetry=self.telemetry,
        )


def _stable_value(value: Any) -> Any:
    if hasattr(value, "value"):
        return _stable_value(value.value)
    if isinstance(value, Mapping):
        return {str(key): _stable_value(value[key]) for key in sorted(value.keys(), key=str)}
    if isinstance(value, (list, tuple)):
        return [_stable_value(item) for item in value]
    if isinstance(value, set):
        return sorted((_stable_value(item) for item in value), key=_stable_json)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _stable_value(value.to_dict())
    if is_dataclass(value):
        return _stable_value(asdict(value))
    return value


def _stable_json(value: Any) -> str:
    return json.dumps(_stable_value(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _stable_hash(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _metadata_tuple(metadata: Mapping[str, Any]) -> Tuple[Tuple[str, Any], ...]:
    return tuple((str(key), _stable_value(value)) for key, value in sorted(metadata.items(), key=lambda item: str(item[0])))


def _metadata_dict(metadata: Tuple[Tuple[str, Any], ...]) -> Dict[str, Any]:
    return {str(key): _stable_value(value) for key, value in metadata}


def _check(check_id: str, passed: bool, explanation: str, details: Mapping[str, Any] | None = None) -> ExecutionReadinessCheck:
    return ExecutionReadinessCheck(str(check_id), bool(passed), str(explanation), _metadata_tuple(details or {}))


def _intake_payload(intake_result: QSeriesExecutionIntakeResult) -> Dict[str, Any]:
    if not isinstance(intake_result, QSeriesExecutionIntakeResult):
        raise TypeError("intake_result must be a QSeriesExecutionIntakeResult")
    payload = intake_result.to_dict()
    if not isinstance(payload, Mapping):
        raise ValueError("intake_result.to_dict() must return a mapping")
    return _stable_value(payload)


def _record_payload(record: Any) -> Dict[str, Any]:
    to_dict = getattr(record, "to_dict", None)
    if not callable(to_dict):
        raise ValueError("intake records must expose to_dict().")
    payload = to_dict()
    if not isinstance(payload, Mapping):
        raise ValueError("record.to_dict() must return a mapping")
    return _stable_value(payload)


def _sorted_records(records: Iterable[Any]) -> Tuple[Any, ...]:
    prepared = [(record, _record_payload(record)) for record in records]
    prepared.sort(key=lambda pair: (str(pair[1].get("intake_hash", "")), str(pair[1].get("intake_id", ""))))
    return tuple(record for record, _payload in prepared)


def _make_readiness(record: Any, intake_result_hash: str, observed_at: str, duplicate_market: bool = False) -> ExecutionReadinessRecord:
    payload = _record_payload(record)
    reasons = []
    if payload.get("status") != "accepted_for_execution_gate_review":
        reasons.append("intake_record_not_accepted")
    if payload.get("read_only") is not True:
        reasons.append("intake_record_not_read_only")
    if payload.get("execution_allowed") is not False:
        reasons.append("intake_record_execution_allowed")
    if payload.get("execution_gate_required") is not True:
        reasons.append("missing_execution_gate_requirement")
    if duplicate_market:
        reasons.append("duplicate_market_intake")

    status = ExecutionReadinessStatus.REJECTED if reasons else ExecutionReadinessStatus.READY_FOR_EXECUTION_GATE
    source_hash = str(payload.get("intake_hash", ""))
    seed = {
        "engine_id": ENGINE_ID,
        "source_intake_id": payload.get("intake_id"),
        "source_intake_hash": source_hash,
        "intake_result_hash": intake_result_hash,
        "status": status.value,
        "reasons": sorted(reasons),
        "observed_at": observed_at,
    }
    readiness_hash = _stable_hash(seed)

    return ExecutionReadinessRecord(
        readiness_id=f"int014_{readiness_hash[:24]}",
        source_intake_id=str(payload.get("intake_id", "unknown_intake")),
        opportunity_id=str(payload.get("opportunity_id", "unknown_opportunity")),
        fingerprint=str(payload.get("fingerprint", "")),
        market_id=str(payload.get("market_id", "unknown_market")),
        venue_id=str(payload.get("venue_id", "unknown_venue")),
        direction=str(payload.get("direction", "UNKNOWN")),
        status=status,
        reasons=tuple(sorted(reasons)),
        source_intake_hash=source_hash,
        readiness_hash=readiness_hash,
        observed_at=str(observed_at),
    )


def _result_hash(*, observed_at: str, status: str, ready_records: Tuple[ExecutionReadinessRecord, ...], rejected_records: Tuple[ExecutionReadinessRecord, ...], checks: Tuple[ExecutionReadinessCheck, ...], pass_count: int, fail_count: int, ready_count: int, rejected_count: int, telemetry: Tuple[Tuple[str, Any], ...]) -> str:
    return _stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "observed_at": observed_at,
            "status": status,
            "ready_records": [record.to_dict() for record in ready_records],
            "rejected_records": [record.to_dict() for record in rejected_records],
            "checks": [check.to_dict() for check in checks],
            "pass_count": pass_count,
            "fail_count": fail_count,
            "ready_count": ready_count,
            "rejected_count": rejected_count,
            "read_only": READ_ONLY,
            "execution_allowed": EXECUTION_ALLOWED,
            "qseries_owned": QSERIES_OWNED,
            "final_execution_gate_required": FINAL_EXECUTION_GATE_REQUIRED,
            "telemetry": _metadata_dict(telemetry),
        }
    )


def review_execution_readiness(*, intake_result: QSeriesExecutionIntakeResult, observed_at: str, limits: ExecutionReadinessLimits | None = None) -> QSeriesExecutionReadinessResult:
    if not str(observed_at).strip():
        raise ValueError("observed_at must be supplied by the caller.")

    limits = limits or ExecutionReadinessLimits()
    intake_payload = _intake_payload(intake_result)
    intake_result_hash = _stable_hash(intake_payload)
    intake_valid = intake_payload.get("schema_version") == "INT-013" and intake_payload.get("passed") is True
    intake_read_only = intake_payload.get("read_only") is True and intake_payload.get("execution_allowed") is False
    intake_gate_required = intake_payload.get("execution_gate_required") is True

    records = _sorted_records(intake_result.records) if intake_valid and intake_read_only and intake_gate_required else tuple()
    market_counts: Dict[str, int] = {}
    for record in records:
        market_id = str(_record_payload(record).get("market_id", ""))
        market_counts[market_id] = market_counts.get(market_id, 0) + 1

    reviewed = tuple(
        _make_readiness(record, intake_result_hash, str(observed_at), duplicate_market=limits.require_unique_markets and market_counts.get(str(_record_payload(record).get("market_id", "")), 0) > 1)
        for record in records[: max(0, limits.max_records)]
    )
    ready = tuple(record for record in reviewed if record.status == ExecutionReadinessStatus.READY_FOR_EXECUTION_GATE)
    rejected = tuple(record for record in reviewed if record.status == ExecutionReadinessStatus.REJECTED)

    checks = (
        _check("int013_intake_valid", intake_valid, "INT-013 execution intake result is passed and usable.", {"schema_version": intake_payload.get("schema_version"), "passed": intake_payload.get("passed")}),
        _check("intake_boundary_read_only", intake_read_only, "INT-013 intake result is read-only and execution-disabled.", {"read_only": intake_payload.get("read_only"), "execution_allowed": intake_payload.get("execution_allowed")}),
        _check("intake_requires_execution_gate", intake_gate_required, "INT-013 intake result requires a later execution gate.", {"execution_gate_required": intake_payload.get("execution_gate_required")}),
        _check("records_within_limits", len(records) <= limits.max_records, "Execution intake record count is within readiness limits.", {"record_count": len(records), "max_records": limits.max_records}),
        _check("ready_records_present", len(ready) > 0, "At least one intake record reached execution-readiness review output.", {"ready_count": len(ready), "rejected_count": len(rejected)}),
        _check("all_intake_records_ready", len(rejected) == 0, "Malformed or unauthorized intake records are blocked from the readiness boundary.", {"ready_count": len(ready), "rejected_count": len(rejected)}),
        _check("no_live_execution", READ_ONLY and not EXECUTION_ALLOWED, "No live execution, exchange call, fund movement, or portfolio mutation occurred.", {"orders_placed": False, "exchange_called": False, "funds_moved": False, "portfolio_mutated": False}),
    )

    pass_count = sum(1 for check in checks if check.passed)
    fail_count = len(checks) - pass_count
    status = "passed" if fail_count == 0 else "failed"
    telemetry = _metadata_tuple(
        {
            "intake_result_hash": intake_result_hash,
            "record_count": len(records),
            "ready_count": len(ready),
            "rejected_count": len(rejected),
            "limits_hash": _stable_hash(limits.to_dict()),
            "read_only": READ_ONLY,
            "execution_allowed": EXECUTION_ALLOWED,
            "final_execution_gate_required": FINAL_EXECUTION_GATE_REQUIRED,
            "orders_placed": False,
            "exchange_calls": False,
            "funds_moved": False,
            "portfolio_mutation": False,
            "files_written": False,
            "databases_written": False,
        }
    )
    readiness_hash = _result_hash(observed_at=str(observed_at), status=status, ready_records=ready, rejected_records=rejected, checks=checks, pass_count=pass_count, fail_count=fail_count, ready_count=len(ready), rejected_count=len(rejected), telemetry=telemetry)
    explanation = "INT-014 completed Q Series risk/readiness review for later execution gate handling." if status == "passed" else "INT-014 blocked readiness because required intake checks failed."

    return QSeriesExecutionReadinessResult(SCHEMA_VERSION, ENGINE_ID, str(observed_at), status, ready, rejected, checks, pass_count, fail_count, len(ready), len(rejected), readiness_hash, READ_ONLY, EXECUTION_ALLOWED, QSERIES_OWNED, FINAL_EXECUTION_GATE_REQUIRED, explanation, telemetry)


def validate_qseries_execution_readiness_result(result: QSeriesExecutionReadinessResult) -> Dict[str, Any]:
    if not isinstance(result, QSeriesExecutionReadinessResult):
        raise TypeError("result must be a QSeriesExecutionReadinessResult")
    checks = {
        "schema_version": result.schema_version == SCHEMA_VERSION,
        "engine_id": result.engine_id == ENGINE_ID,
        "read_only": result.read_only is True,
        "execution_disabled": result.execution_allowed is False,
        "qseries_owned": result.qseries_owned is True,
        "final_execution_gate_required": result.final_execution_gate_required is True,
        "hash_valid": result.verify_readiness_hash(),
        "record_boundaries": all(record.read_only and not record.execution_allowed and record.final_execution_gate_required for record in result.ready_records + result.rejected_records),
    }
    return {"passed": all(checks.values()) and result.passed, "checks": checks, "result": result.to_dict()}


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "READ_ONLY",
    "EXECUTION_ALLOWED",
    "QSERIES_OWNED",
    "FINAL_EXECUTION_GATE_REQUIRED",
    "ExecutionReadinessStatus",
    "ExecutionReadinessLimits",
    "ExecutionReadinessRecord",
    "ExecutionReadinessCheck",
    "QSeriesExecutionReadinessResult",
    "review_execution_readiness",
    "validate_qseries_execution_readiness_result",
]

