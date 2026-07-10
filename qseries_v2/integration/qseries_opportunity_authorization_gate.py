"""
INT-012 Q Series Opportunity Authorization Gate

Q Series-owned read-only authorization review for validated OOS opportunities.
This gate never places orders, calls venues, mutates portfolios, or moves funds.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple


SCHEMA_VERSION = "INT-012"
ENGINE_ID = "INT-012"
READ_ONLY = True
EXECUTION_ALLOWED = False
QSERIES_OWNED = True


class OpportunityAuthorizationStatus(str, Enum):
    AUTHORIZED_FOR_REVIEW = "authorized_for_execution_review"
    REJECTED = "rejected"
    HOLD = "hold"


@dataclass(frozen=True)
class OpportunityAuthorizationLimits:
    min_confidence: float = 0.70
    min_abs_expected_edge: float = 0.01
    min_liquidity_score: float = 0.20
    max_risk_score: float = 0.35
    max_execution_difficulty: float = 0.70
    require_execution_adapter: bool = True
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OpportunityAuthorizationDecision:
    decision_id: str
    opportunity_id: str
    fingerprint: str
    market_id: str
    venue_id: str
    direction: str
    status: OpportunityAuthorizationStatus
    reasons: Tuple[str, ...]
    opportunity_hash: str
    authorization_hash: str
    read_only: bool = READ_ONLY
    execution_allowed: bool = EXECUTION_ALLOWED
    qseries_owned: bool = QSERIES_OWNED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "opportunity_id": self.opportunity_id,
            "fingerprint": self.fingerprint,
            "market_id": self.market_id,
            "venue_id": self.venue_id,
            "direction": self.direction,
            "status": self.status.value,
            "reasons": list(self.reasons),
            "opportunity_hash": self.opportunity_hash,
            "authorization_hash": self.authorization_hash,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "qseries_owned": self.qseries_owned,
        }


@dataclass(frozen=True)
class OpportunityAuthorizationCheck:
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
class QSeriesOpportunityAuthorizationResult:
    schema_version: str
    engine_id: str
    observed_at: str
    status: str
    decisions: Tuple[OpportunityAuthorizationDecision, ...]
    checks: Tuple[OpportunityAuthorizationCheck, ...]
    pass_count: int
    fail_count: int
    authorized_count: int
    rejected_count: int
    hold_count: int
    authorization_hash: str
    read_only: bool
    execution_allowed: bool
    qseries_owned: bool
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
            "decisions": [decision.to_dict() for decision in self.decisions],
            "checks": [check.to_dict() for check in self.checks],
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "authorized_count": self.authorized_count,
            "rejected_count": self.rejected_count,
            "hold_count": self.hold_count,
            "authorization_hash": self.authorization_hash,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "qseries_owned": self.qseries_owned,
            "explanation": self.explanation,
            "telemetry": _metadata_dict(self.telemetry),
            "passed": self.passed,
        }

    def verify_authorization_hash(self) -> bool:
        return self.authorization_hash == _result_hash(
            observed_at=self.observed_at,
            status=self.status,
            decisions=self.decisions,
            checks=self.checks,
            pass_count=self.pass_count,
            fail_count=self.fail_count,
            authorized_count=self.authorized_count,
            rejected_count=self.rejected_count,
            hold_count=self.hold_count,
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


def _check(check_id: str, passed: bool, explanation: str, details: Optional[Mapping[str, Any]] = None) -> OpportunityAuthorizationCheck:
    return OpportunityAuthorizationCheck(str(check_id), bool(passed), str(explanation), _metadata_tuple(details or {}))


def _opportunity_payload(opportunity: Any) -> Dict[str, Any]:
    if not bool(getattr(opportunity, "read_only", False)):
        raise ValueError("INT-012 accepts read-only UniversalOpportunity fixtures only.")
    to_dict = getattr(opportunity, "to_dict", None)
    fingerprint = getattr(opportunity, "fingerprint", None)
    if not callable(to_dict) or not callable(fingerprint):
        raise ValueError("INT-012 requires UniversalOpportunity-style objects with to_dict() and fingerprint().")
    payload = to_dict()
    if not isinstance(payload, Mapping):
        raise ValueError("opportunity.to_dict() must return a mapping.")
    canonical = _stable_value(payload)
    if not isinstance(canonical, dict):
        raise ValueError("canonical opportunity payload must be a mapping.")
    canonical["fingerprint"] = str(fingerprint())
    return canonical


def _sorted_opportunities(opportunities: Iterable[Any]) -> Tuple[Any, ...]:
    prepared = [(item, _opportunity_payload(item)) for item in opportunities]
    prepared.sort(key=lambda pair: (str(pair[1].get("fingerprint", "")), str(pair[1].get("opportunity_id", "")), _stable_json(pair[1])))
    return tuple(item for item, _payload in prepared)


def _oos_payload(oos_result: Any) -> Dict[str, Any]:
    to_dict = getattr(oos_result, "to_dict", None)
    if not callable(to_dict):
        raise ValueError("oos_result must expose to_dict().")
    payload = to_dict()
    if not isinstance(payload, Mapping):
        raise ValueError("oos_result.to_dict() must return a mapping.")
    return _stable_value(payload)


def _enum_value(value: Any) -> str:
    return str(value.value) if hasattr(value, "value") else str(value)


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _evaluate_opportunity(opportunity: Any, limits: OpportunityAuthorizationLimits, oos_hash: str) -> OpportunityAuthorizationDecision:
    payload = _opportunity_payload(opportunity)
    opportunity_hash = _stable_hash(payload)
    reasons = []

    if bool(payload.get("read_only")) is not True:
        reasons.append("opportunity_not_read_only")
    if _enum_value(getattr(opportunity, "status", "")) not in {"new", "verified", "ranked"}:
        reasons.append("opportunity_status_not_reviewable")
    if _enum_value(getattr(opportunity, "direction", "")) in {"HOLD", "UNKNOWN"}:
        reasons.append("direction_not_authorizable")
    if _float(getattr(opportunity, "confidence", None)) < limits.min_confidence:
        reasons.append("confidence_below_limit")
    if abs(_float(getattr(opportunity, "expected_edge", None))) < limits.min_abs_expected_edge:
        reasons.append("expected_edge_below_limit")
    if _float(getattr(opportunity, "liquidity_score", None)) < limits.min_liquidity_score:
        reasons.append("liquidity_below_limit")
    if _float(getattr(opportunity, "risk_score", None), 1.0) > limits.max_risk_score:
        reasons.append("risk_above_limit")

    execution = getattr(opportunity, "execution", None)
    adapter = getattr(execution, "required_execution_adapter", None)
    if limits.require_execution_adapter and not str(adapter or "").strip():
        reasons.append("missing_execution_adapter")
    if _float(getattr(execution, "execution_difficulty", None), 1.0) > limits.max_execution_difficulty:
        reasons.append("execution_difficulty_above_limit")

    if reasons:
        status = OpportunityAuthorizationStatus.REJECTED
    else:
        status = OpportunityAuthorizationStatus.AUTHORIZED_FOR_REVIEW

    seed = {
        "engine_id": ENGINE_ID,
        "opportunity_hash": opportunity_hash,
        "limits": limits.to_dict(),
        "oos_hash": oos_hash,
    }
    auth_hash = _stable_hash(seed)

    return OpportunityAuthorizationDecision(
        decision_id=f"int012_{auth_hash[:24]}",
        opportunity_id=str(payload.get("opportunity_id", "unknown_opportunity")),
        fingerprint=str(payload.get("fingerprint", "")),
        market_id=str(payload.get("market_id", "unknown_market")),
        venue_id=str(payload.get("venue_id", "unknown_venue")),
        direction=str(payload.get("direction", "UNKNOWN")),
        status=status,
        reasons=tuple(sorted(reasons)),
        opportunity_hash=opportunity_hash,
        authorization_hash=auth_hash,
    )


def _result_hash(*, observed_at: str, status: str, decisions: Tuple[OpportunityAuthorizationDecision, ...], checks: Tuple[OpportunityAuthorizationCheck, ...], pass_count: int, fail_count: int, authorized_count: int, rejected_count: int, hold_count: int, telemetry: Tuple[Tuple[str, Any], ...]) -> str:
    return _stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "observed_at": observed_at,
            "status": status,
            "decisions": [decision.to_dict() for decision in decisions],
            "checks": [check.to_dict() for check in checks],
            "pass_count": pass_count,
            "fail_count": fail_count,
            "authorized_count": authorized_count,
            "rejected_count": rejected_count,
            "hold_count": hold_count,
            "read_only": READ_ONLY,
            "execution_allowed": EXECUTION_ALLOWED,
            "qseries_owned": QSERIES_OWNED,
            "telemetry": _metadata_dict(telemetry),
        }
    )


def authorize_oos_opportunities(opportunities: Iterable[Any], *, oos_result: Any, observed_at: str, limits: Optional[OpportunityAuthorizationLimits] = None) -> QSeriesOpportunityAuthorizationResult:
    if not str(observed_at).strip():
        raise ValueError("observed_at must be supplied by the caller.")

    limits = limits or OpportunityAuthorizationLimits()
    opportunities = _sorted_opportunities(tuple(opportunities))
    oos_payload = _oos_payload(oos_result)
    oos_hash = _stable_hash(oos_payload)

    oos_passed = oos_payload.get("schema_version") == "OOS-005" and oos_payload.get("passed") is True
    oos_read_only = oos_payload.get("read_only") is True and oos_payload.get("execution_allowed") is False

    decisions = tuple(_evaluate_opportunity(item, limits, oos_hash) for item in opportunities) if oos_passed and oos_read_only else tuple()
    authorized_count = sum(1 for item in decisions if item.status == OpportunityAuthorizationStatus.AUTHORIZED_FOR_REVIEW)
    rejected_count = sum(1 for item in decisions if item.status == OpportunityAuthorizationStatus.REJECTED)
    hold_count = sum(1 for item in decisions if item.status == OpportunityAuthorizationStatus.HOLD)

    checks = (
        _check("oos_005_passed", oos_passed, "OOS-005 opportunity subsystem gate passed.", {"oos_schema_version": oos_payload.get("schema_version"), "oos_passed": oos_payload.get("passed")}),
        _check("oos_read_only_boundary", oos_read_only, "OOS result is read-only and execution-disabled.", {"oos_read_only": oos_payload.get("read_only"), "oos_execution_allowed": oos_payload.get("execution_allowed")}),
        _check("opportunity_inputs_present", len(opportunities) > 0, "At least one validated opportunity fixture is present.", {"input_count": len(opportunities)}),
        _check("authorization_decisions_created", len(decisions) == len(opportunities) and bool(decisions), "Every input opportunity received a Q Series review decision.", {"decision_count": len(decisions), "input_count": len(opportunities)}),
        _check("qseries_review_only", READ_ONLY and not EXECUTION_ALLOWED and QSERIES_OWNED, "Q Series owns authorization review; execution remains disabled.", {"read_only": READ_ONLY, "execution_allowed": EXECUTION_ALLOWED, "qseries_owned": QSERIES_OWNED, "orders_placed": False, "portfolio_mutated": False, "exchange_called": False}),
    )

    pass_count = sum(1 for check in checks if check.passed)
    fail_count = len(checks) - pass_count
    status = "passed" if fail_count == 0 else "failed"
    telemetry = _metadata_tuple(
        {
            "input_count": len(opportunities),
            "authorized_count": authorized_count,
            "rejected_count": rejected_count,
            "hold_count": hold_count,
            "oos_hash": oos_hash,
            "limits_hash": _stable_hash(limits.to_dict()),
            "read_only": READ_ONLY,
            "execution_allowed": EXECUTION_ALLOWED,
            "orders_placed": False,
            "exchange_calls": False,
            "portfolio_mutation": False,
            "files_written": False,
            "databases_written": False,
        }
    )
    authorization_hash = _result_hash(observed_at=str(observed_at), status=status, decisions=decisions, checks=checks, pass_count=pass_count, fail_count=fail_count, authorized_count=authorized_count, rejected_count=rejected_count, hold_count=hold_count, telemetry=telemetry)
    explanation = "INT-012 produced Q Series review authorization decisions without execution." if status == "passed" else "INT-012 blocked authorization because required handoff checks failed."

    return QSeriesOpportunityAuthorizationResult(SCHEMA_VERSION, ENGINE_ID, str(observed_at), status, decisions, checks, pass_count, fail_count, authorized_count, rejected_count, hold_count, authorization_hash, READ_ONLY, EXECUTION_ALLOWED, QSERIES_OWNED, explanation, telemetry)


def validate_qseries_opportunity_authorization_result(result: QSeriesOpportunityAuthorizationResult) -> Dict[str, Any]:
    if not isinstance(result, QSeriesOpportunityAuthorizationResult):
        raise TypeError("result must be a QSeriesOpportunityAuthorizationResult")
    checks = {
        "schema_version": result.schema_version == SCHEMA_VERSION,
        "engine_id": result.engine_id == ENGINE_ID,
        "read_only": result.read_only is True,
        "execution_disabled": result.execution_allowed is False,
        "qseries_owned": result.qseries_owned is True,
        "hash_valid": result.verify_authorization_hash(),
        "decision_boundaries": all(decision.read_only and not decision.execution_allowed and decision.qseries_owned for decision in result.decisions),
    }
    return {"passed": all(checks.values()) and result.passed, "checks": checks, "result": result.to_dict()}


def assert_qseries_opportunity_authorization_read_only(result: QSeriesOpportunityAuthorizationResult) -> bool:
    validation = validate_qseries_opportunity_authorization_result(result)
    return validation["checks"]["read_only"] and validation["checks"]["execution_disabled"] and validation["checks"]["decision_boundaries"]


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "READ_ONLY",
    "EXECUTION_ALLOWED",
    "QSERIES_OWNED",
    "OpportunityAuthorizationStatus",
    "OpportunityAuthorizationLimits",
    "OpportunityAuthorizationDecision",
    "OpportunityAuthorizationCheck",
    "QSeriesOpportunityAuthorizationResult",
    "authorize_oos_opportunities",
    "validate_qseries_opportunity_authorization_result",
    "assert_qseries_opportunity_authorization_read_only",
]
