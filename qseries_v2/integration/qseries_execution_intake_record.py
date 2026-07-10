"""
INT-013 Q Series Execution Intake Record

Transforms authorized INT-012 opportunity decisions into immutable Q Series
execution-intake proposals. This module never places orders, calls exchanges,
moves funds, or mutates portfolios.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Dict, Iterable, Mapping, Tuple

from qseries_v2.integration.qseries_opportunity_authorization_gate import (
    QSeriesOpportunityAuthorizationResult,
)


SCHEMA_VERSION = "INT-013"
ENGINE_ID = "INT-013"
READ_ONLY = True
EXECUTION_ALLOWED = False
QSERIES_OWNED = True
EXECUTION_GATE_REQUIRED = True


class ExecutionIntakeStatus(str, Enum):
    ACCEPTED = "accepted_for_execution_gate_review"
    REJECTED = "rejected"


@dataclass(frozen=True)
class QSeriesExecutionIntakeRecord:
    intake_id: str
    source_decision_id: str
    opportunity_id: str
    fingerprint: str
    market_id: str
    venue_id: str
    direction: str
    status: ExecutionIntakeStatus
    reasons: Tuple[str, ...]
    source_authorization_hash: str
    intake_hash: str
    observed_at: str
    read_only: bool = READ_ONLY
    execution_allowed: bool = EXECUTION_ALLOWED
    qseries_owned: bool = QSERIES_OWNED
    execution_gate_required: bool = EXECUTION_GATE_REQUIRED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intake_id": self.intake_id,
            "source_decision_id": self.source_decision_id,
            "opportunity_id": self.opportunity_id,
            "fingerprint": self.fingerprint,
            "market_id": self.market_id,
            "venue_id": self.venue_id,
            "direction": self.direction,
            "status": self.status.value,
            "reasons": list(self.reasons),
            "source_authorization_hash": self.source_authorization_hash,
            "intake_hash": self.intake_hash,
            "observed_at": self.observed_at,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "qseries_owned": self.qseries_owned,
            "execution_gate_required": self.execution_gate_required,
        }


@dataclass(frozen=True)
class QSeriesExecutionIntakeCheck:
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
class QSeriesExecutionIntakeResult:
    schema_version: str
    engine_id: str
    observed_at: str
    status: str
    records: Tuple[QSeriesExecutionIntakeRecord, ...]
    rejected_decisions: Tuple[QSeriesExecutionIntakeRecord, ...]
    checks: Tuple[QSeriesExecutionIntakeCheck, ...]
    pass_count: int
    fail_count: int
    accepted_count: int
    rejected_count: int
    intake_hash: str
    read_only: bool
    execution_allowed: bool
    qseries_owned: bool
    execution_gate_required: bool
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
            "records": [record.to_dict() for record in self.records],
            "rejected_decisions": [record.to_dict() for record in self.rejected_decisions],
            "checks": [check.to_dict() for check in self.checks],
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "intake_hash": self.intake_hash,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "qseries_owned": self.qseries_owned,
            "execution_gate_required": self.execution_gate_required,
            "explanation": self.explanation,
            "telemetry": _metadata_dict(self.telemetry),
            "passed": self.passed,
        }

    def verify_intake_hash(self) -> bool:
        return self.intake_hash == _result_hash(
            observed_at=self.observed_at,
            status=self.status,
            records=self.records,
            rejected_decisions=self.rejected_decisions,
            checks=self.checks,
            pass_count=self.pass_count,
            fail_count=self.fail_count,
            accepted_count=self.accepted_count,
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


def _check(check_id: str, passed: bool, explanation: str, details: Mapping[str, Any] | None = None) -> QSeriesExecutionIntakeCheck:
    return QSeriesExecutionIntakeCheck(str(check_id), bool(passed), str(explanation), _metadata_tuple(details or {}))


def _authorization_payload(authorization_result: QSeriesOpportunityAuthorizationResult) -> Dict[str, Any]:
    if not isinstance(authorization_result, QSeriesOpportunityAuthorizationResult):
        raise TypeError("authorization_result must be a QSeriesOpportunityAuthorizationResult")
    payload = authorization_result.to_dict()
    if not isinstance(payload, Mapping):
        raise ValueError("authorization_result.to_dict() must return a mapping")
    return _stable_value(payload)


def _decision_payload(decision: Any) -> Dict[str, Any]:
    to_dict = getattr(decision, "to_dict", None)
    if not callable(to_dict):
        raise ValueError("authorization decisions must expose to_dict().")
    payload = to_dict()
    if not isinstance(payload, Mapping):
        raise ValueError("decision.to_dict() must return a mapping.")
    return _stable_value(payload)


def _sorted_decisions(decisions: Iterable[Any]) -> Tuple[Any, ...]:
    prepared = [(decision, _decision_payload(decision)) for decision in decisions]
    prepared.sort(key=lambda pair: (str(pair[1].get("authorization_hash", "")), str(pair[1].get("decision_id", ""))))
    return tuple(decision for decision, _payload in prepared)


def _make_record(decision: Any, authorization_hash: str, observed_at: str) -> QSeriesExecutionIntakeRecord:
    payload = _decision_payload(decision)
    decision_status = str(payload.get("status", ""))
    accepted = decision_status == "authorized_for_execution_review"
    status = ExecutionIntakeStatus.ACCEPTED if accepted else ExecutionIntakeStatus.REJECTED
    reasons = tuple(sorted(str(item) for item in payload.get("reasons", []) or []))
    if not accepted and not reasons:
        reasons = ("authorization_status_not_accepted",)

    seed = {
        "engine_id": ENGINE_ID,
        "source_decision_id": payload.get("decision_id"),
        "source_authorization_hash": payload.get("authorization_hash"),
        "authorization_result_hash": authorization_hash,
        "status": status.value,
        "observed_at": observed_at,
    }
    intake_hash = _stable_hash(seed)

    return QSeriesExecutionIntakeRecord(
        intake_id=f"int013_{intake_hash[:24]}",
        source_decision_id=str(payload.get("decision_id", "unknown_decision")),
        opportunity_id=str(payload.get("opportunity_id", "unknown_opportunity")),
        fingerprint=str(payload.get("fingerprint", "")),
        market_id=str(payload.get("market_id", "unknown_market")),
        venue_id=str(payload.get("venue_id", "unknown_venue")),
        direction=str(payload.get("direction", "UNKNOWN")),
        status=status,
        reasons=reasons,
        source_authorization_hash=str(payload.get("authorization_hash", "")),
        intake_hash=intake_hash,
        observed_at=str(observed_at),
    )


def _result_hash(*, observed_at: str, status: str, records: Tuple[QSeriesExecutionIntakeRecord, ...], rejected_decisions: Tuple[QSeriesExecutionIntakeRecord, ...], checks: Tuple[QSeriesExecutionIntakeCheck, ...], pass_count: int, fail_count: int, accepted_count: int, rejected_count: int, telemetry: Tuple[Tuple[str, Any], ...]) -> str:
    return _stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "observed_at": observed_at,
            "status": status,
            "records": [record.to_dict() for record in records],
            "rejected_decisions": [record.to_dict() for record in rejected_decisions],
            "checks": [check.to_dict() for check in checks],
            "pass_count": pass_count,
            "fail_count": fail_count,
            "accepted_count": accepted_count,
            "rejected_count": rejected_count,
            "read_only": READ_ONLY,
            "execution_allowed": EXECUTION_ALLOWED,
            "qseries_owned": QSERIES_OWNED,
            "execution_gate_required": EXECUTION_GATE_REQUIRED,
            "telemetry": _metadata_dict(telemetry),
        }
    )


def build_qseries_execution_intake_records(*, authorization_result: QSeriesOpportunityAuthorizationResult, observed_at: str) -> QSeriesExecutionIntakeResult:
    if not str(observed_at).strip():
        raise ValueError("observed_at must be supplied by the caller.")

    auth_payload = _authorization_payload(authorization_result)
    authorization_hash = _stable_hash(auth_payload)
    auth_valid = auth_payload.get("schema_version") == "INT-012" and auth_payload.get("passed") is True
    auth_read_only = auth_payload.get("read_only") is True and auth_payload.get("execution_allowed") is False
    auth_qseries_owned = auth_payload.get("qseries_owned") is True

    decisions = _sorted_decisions(authorization_result.decisions)
    all_records = tuple(_make_record(decision, authorization_hash, str(observed_at)) for decision in decisions) if auth_valid and auth_read_only and auth_qseries_owned else tuple()
    records = tuple(record for record in all_records if record.status == ExecutionIntakeStatus.ACCEPTED)
    rejected = tuple(record for record in all_records if record.status == ExecutionIntakeStatus.REJECTED)

    checks = (
        _check("int012_authorization_valid", auth_valid, "INT-012 authorization result is passed and usable.", {"schema_version": auth_payload.get("schema_version"), "passed": auth_payload.get("passed")}),
        _check("authorization_boundary_read_only", auth_read_only, "Authorization result is read-only and execution-disabled.", {"read_only": auth_payload.get("read_only"), "execution_allowed": auth_payload.get("execution_allowed")}),
        _check("qseries_ownership", auth_qseries_owned, "Authorization result is Q Series-owned.", {"qseries_owned": auth_payload.get("qseries_owned")}),
        _check("authorized_records_present", len(records) > 0, "At least one authorized decision became an execution-intake proposal.", {"accepted_count": len(records), "rejected_count": len(rejected)}),
        _check("execution_gate_required", EXECUTION_GATE_REQUIRED and not EXECUTION_ALLOWED, "Output remains a proposal requiring a later execution gate.", {"execution_gate_required": EXECUTION_GATE_REQUIRED, "execution_allowed": EXECUTION_ALLOWED}),
        _check("no_live_execution", READ_ONLY and not EXECUTION_ALLOWED, "No live execution, exchange call, fund movement, or portfolio mutation occurred.", {"orders_placed": False, "exchange_called": False, "funds_moved": False, "portfolio_mutated": False}),
    )

    pass_count = sum(1 for check in checks if check.passed)
    fail_count = len(checks) - pass_count
    status = "passed" if fail_count == 0 else "failed"
    telemetry = _metadata_tuple(
        {
            "authorization_hash": authorization_hash,
            "decision_count": len(decisions),
            "accepted_count": len(records),
            "rejected_count": len(rejected),
            "read_only": READ_ONLY,
            "execution_allowed": EXECUTION_ALLOWED,
            "execution_gate_required": EXECUTION_GATE_REQUIRED,
            "orders_placed": False,
            "exchange_calls": False,
            "funds_moved": False,
            "portfolio_mutation": False,
            "files_written": False,
            "databases_written": False,
        }
    )
    intake_hash = _result_hash(observed_at=str(observed_at), status=status, records=records, rejected_decisions=rejected, checks=checks, pass_count=pass_count, fail_count=fail_count, accepted_count=len(records), rejected_count=len(rejected), telemetry=telemetry)
    explanation = "INT-013 created Q Series execution-intake proposals requiring a later execution gate." if status == "passed" else "INT-013 blocked execution intake because required authorization checks failed."

    return QSeriesExecutionIntakeResult(SCHEMA_VERSION, ENGINE_ID, str(observed_at), status, records, rejected, checks, pass_count, fail_count, len(records), len(rejected), intake_hash, READ_ONLY, EXECUTION_ALLOWED, QSERIES_OWNED, EXECUTION_GATE_REQUIRED, explanation, telemetry)


def validate_qseries_execution_intake_result(result: QSeriesExecutionIntakeResult) -> Dict[str, Any]:
    if not isinstance(result, QSeriesExecutionIntakeResult):
        raise TypeError("result must be a QSeriesExecutionIntakeResult")
    checks = {
        "schema_version": result.schema_version == SCHEMA_VERSION,
        "engine_id": result.engine_id == ENGINE_ID,
        "read_only": result.read_only is True,
        "execution_disabled": result.execution_allowed is False,
        "qseries_owned": result.qseries_owned is True,
        "execution_gate_required": result.execution_gate_required is True,
        "hash_valid": result.verify_intake_hash(),
        "record_boundaries": all(record.read_only and not record.execution_allowed and record.execution_gate_required for record in result.records + result.rejected_decisions),
    }
    return {"passed": all(checks.values()) and result.passed, "checks": checks, "result": result.to_dict()}


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "READ_ONLY",
    "EXECUTION_ALLOWED",
    "QSERIES_OWNED",
    "EXECUTION_GATE_REQUIRED",
    "ExecutionIntakeStatus",
    "QSeriesExecutionIntakeRecord",
    "QSeriesExecutionIntakeCheck",
    "QSeriesExecutionIntakeResult",
    "build_qseries_execution_intake_records",
    "validate_qseries_execution_intake_result",
]
