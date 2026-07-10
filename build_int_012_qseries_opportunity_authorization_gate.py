from pathlib import Path


ROOT = Path.cwd()
INTEGRATION = ROOT / "qseries_v2" / "integration"
MODULE_PATH = INTEGRATION / "qseries_opportunity_authorization_gate.py"
INIT_PATH = INTEGRATION / "__init__.py"
TEST_PATH = ROOT / "test_int_012_qseries_opportunity_authorization_gate.py"

MODULE_CODE = r'''"""
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
'''

TEST_CODE = r'''from dataclasses import FrozenInstanceError
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from qseries_v2.integration import authorize_oos_opportunities as exported_authorize
from qseries_v2.integration.qseries_opportunity_authorization_gate import (
    ENGINE_ID,
    EXECUTION_ALLOWED,
    READ_ONLY,
    SCHEMA_VERSION,
    OpportunityAuthorizationLimits,
    OpportunityAuthorizationStatus,
    QSeriesOpportunityAuthorizationResult,
    assert_qseries_opportunity_authorization_read_only,
    authorize_oos_opportunities,
    validate_qseries_opportunity_authorization_result,
)
from qseries_v2.oracle_intelligence.opportunity_operating_system import run_opportunity_subsystem_integration_gate
from qseries_v2.oracle_intelligence.universal_market_model import UniversalMarketFactory
from qseries_v2.oracle_intelligence.universal_opportunity_model import (
    OpportunityExecutionProfile,
    OpportunityTimeWindow,
    UniversalOpportunityFactory,
)


ROOT = Path(__file__).resolve().parent
OBSERVED_AT = "2026-07-10T21:00:00+00:00"


def _market(market_id="KXINT012-YES"):
    return UniversalMarketFactory.from_prediction_market(
        venue_id="kalshi",
        venue_name="Kalshi",
        market_id=market_id,
        title=f"Prediction market {market_id}",
        bid=0.52,
        ask=0.55,
        liquidity=30000,
    )


def _opportunity(market_id="KXINT012-YES", edge=0.12, confidence=0.84, risk=0.25, liquidity=0.76, difficulty=0.25):
    return UniversalOpportunityFactory.prediction_market_scalp(
        market=_market(market_id),
        fair_value=0.55 + edge,
        market_price=0.55,
        confidence=confidence,
        explanation=f"Q Series review fixture for {market_id}.",
        liquidity_score=liquidity,
        risk_score=risk,
        time_window=OpportunityTimeWindow(urgency_score=0.50, freshness_score=1.0),
        execution=OpportunityExecutionProfile(
            required_execution_adapter="prediction_market",
            execution_difficulty=difficulty,
            capital_required=100,
        ),
    )


def _opportunities():
    return (
        _opportunity("KXINT012-A", edge=0.08, confidence=0.78, risk=0.22),
        _opportunity("KXINT012-B", edge=0.16, confidence=0.90, risk=0.18),
        _opportunity("KXINT012-C", edge=0.12, confidence=0.84, risk=0.30),
    )


def _oos_result(opportunities):
    return run_opportunity_subsystem_integration_gate(opportunities, observed_at=OBSERVED_AT)


def test_int_012_authorizes_valid_oos_opportunities_for_review_only():
    opportunities = _opportunities()
    result = authorize_oos_opportunities(opportunities, oos_result=_oos_result(opportunities), observed_at=OBSERVED_AT)

    assert isinstance(result, QSeriesOpportunityAuthorizationResult)
    assert result.schema_version == "INT-012"
    assert result.engine_id == "INT-012"
    assert result.status == "passed"
    assert result.passed is True
    assert result.authorized_count == 3
    assert result.rejected_count == 0
    assert all(decision.status == OpportunityAuthorizationStatus.AUTHORIZED_FOR_REVIEW for decision in result.decisions)
    assert all(decision.execution_allowed is False for decision in result.decisions)


def test_int_012_rejects_risky_or_weak_opportunities():
    opportunities = (
        _opportunity("LOWCONF", confidence=0.40),
        _opportunity("HIGHRISK", risk=0.90),
        _opportunity("LOWEDGE", edge=0.001),
    )
    oos_result = _oos_result(opportunities)
    result = authorize_oos_opportunities(opportunities, oos_result=oos_result, observed_at=OBSERVED_AT)

    assert result.status == "passed"
    assert result.authorized_count == 0
    assert result.rejected_count == 3
    reasons = {reason for decision in result.decisions for reason in decision.reasons}
    assert "confidence_below_limit" in reasons
    assert "risk_above_limit" in reasons
    assert "expected_edge_below_limit" in reasons


def test_int_012_blocks_failed_oos_gate():
    opportunities = _opportunities()
    failed_oos = dict(_oos_result(opportunities).to_dict())
    failed_oos["passed"] = False

    class FailedOOS:
        def to_dict(self):
            return failed_oos

    result = authorize_oos_opportunities(opportunities, oos_result=FailedOOS(), observed_at=OBSERVED_AT)

    assert result.status == "failed"
    assert result.fail_count >= 1
    assert result.decisions == tuple()
    check_map = {check.check_id: check for check in result.checks}
    assert check_map["oos_005_passed"].passed is False


def test_int_012_deterministic_hash():
    opportunities = _opportunities()
    oos_result = _oos_result(opportunities)
    first = authorize_oos_opportunities(opportunities, oos_result=oos_result, observed_at=OBSERVED_AT)
    second = authorize_oos_opportunities(opportunities, oos_result=oos_result, observed_at=OBSERVED_AT)

    assert first.authorization_hash == second.authorization_hash
    assert first.to_dict() == second.to_dict()
    assert first.verify_authorization_hash() is True


def test_int_012_order_independent_hash():
    opportunities = _opportunities()
    oos_result = _oos_result(opportunities)
    first = authorize_oos_opportunities(opportunities, oos_result=oos_result, observed_at=OBSERVED_AT)
    second = authorize_oos_opportunities(tuple(reversed(opportunities)), oos_result=oos_result, observed_at=OBSERVED_AT)

    assert first.authorization_hash == second.authorization_hash
    assert [d.decision_id for d in first.decisions] == [d.decision_id for d in second.decisions]


def test_int_012_frozen_and_json_serializable():
    opportunities = _opportunities()
    result = authorize_oos_opportunities(opportunities, oos_result=_oos_result(opportunities), observed_at=OBSERVED_AT)

    try:
        result.status = "failed"
        raise AssertionError("QSeriesOpportunityAuthorizationResult must be frozen.")
    except FrozenInstanceError:
        pass

    encoded = json.dumps(result.to_dict(), sort_keys=True)
    assert '"schema_version": "INT-012"' in encoded


def test_int_012_read_only_execution_disabled():
    opportunities = _opportunities()
    result = authorize_oos_opportunities(opportunities, oos_result=_oos_result(opportunities), observed_at=OBSERVED_AT)

    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert result.read_only is True
    assert result.execution_allowed is False
    assert assert_qseries_opportunity_authorization_read_only(result) is True
    assert dict(result.telemetry)["orders_placed"] is False
    assert dict(result.telemetry)["exchange_calls"] is False
    assert dict(result.telemetry)["portfolio_mutation"] is False


def test_int_012_validation_helper_and_package_export():
    opportunities = _opportunities()
    result = exported_authorize(opportunities, oos_result=_oos_result(opportunities), observed_at=OBSERVED_AT)
    validation = validate_qseries_opportunity_authorization_result(result)

    assert validation["passed"] is True
    assert all(validation["checks"].values())
    assert ENGINE_ID == "INT-012"
    assert SCHEMA_VERSION == "INT-012"


def test_int_012_custom_limits_reject():
    opportunities = _opportunities()
    strict = OpportunityAuthorizationLimits(min_confidence=0.95)
    result = authorize_oos_opportunities(opportunities, oos_result=_oos_result(opportunities), observed_at=OBSERVED_AT, limits=strict)

    assert result.rejected_count == 3
    assert all("confidence_below_limit" in decision.reasons for decision in result.decisions)


def test_int_012_requires_caller_observed_at():
    opportunities = _opportunities()
    try:
        authorize_oos_opportunities(opportunities, oos_result=_oos_result(opportunities), observed_at="")
        raise AssertionError("observed_at must be caller supplied.")
    except ValueError:
        pass


def test_int_012_no_filesystem_or_database_writes():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        before = sorted(path.relative_to(root) for path in root.rglob("*"))
        opportunities = _opportunities()
        result = authorize_oos_opportunities(opportunities, oos_result=_oos_result(opportunities), observed_at=OBSERVED_AT)
        after = sorted(path.relative_to(root) for path in root.rglob("*"))

    assert before == after
    assert dict(result.telemetry)["files_written"] is False
    assert dict(result.telemetry)["databases_written"] is False


def test_int_012_installer_is_idempotent():
    tracked = (
        ROOT / "build_int_012_qseries_opportunity_authorization_gate.py",
        ROOT / "qseries_v2" / "integration" / "qseries_opportunity_authorization_gate.py",
        ROOT / "test_int_012_qseries_opportunity_authorization_gate.py",
        ROOT / "qseries_v2" / "integration" / "__init__.py",
    )
    before = {path: path.read_text(encoding="utf-8") for path in tracked}
    subprocess.run(
        [sys.executable, str(ROOT / "build_int_012_qseries_opportunity_authorization_gate.py")],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    after = {path: path.read_text(encoding="utf-8") for path in tracked}
    assert before == after


if __name__ == "__main__":
    test_int_012_authorizes_valid_oos_opportunities_for_review_only()
    test_int_012_rejects_risky_or_weak_opportunities()
    test_int_012_blocks_failed_oos_gate()
    test_int_012_deterministic_hash()
    test_int_012_order_independent_hash()
    test_int_012_frozen_and_json_serializable()
    test_int_012_read_only_execution_disabled()
    test_int_012_validation_helper_and_package_export()
    test_int_012_custom_limits_reject()
    test_int_012_requires_caller_observed_at()
    test_int_012_no_filesystem_or_database_writes()
    test_int_012_installer_is_idempotent()

    opportunities = _opportunities()
    result = authorize_oos_opportunities(opportunities, oos_result=_oos_result(opportunities), observed_at=OBSERVED_AT)
    print("[PASS] INT-012 Q Series Opportunity Authorization Gate")
    print(
        {
            "schema_version": result.schema_version,
            "engine_id": result.engine_id,
            "status": result.status,
            "authorized_count": result.authorized_count,
            "rejected_count": result.rejected_count,
            "read_only": result.read_only,
            "execution_allowed": result.execution_allowed,
        }
    )
'''

EXPORT_BLOCK = '''from .qseries_opportunity_authorization_gate import (
    SCHEMA_VERSION as QSERIES_OPPORTUNITY_AUTHORIZATION_SCHEMA_VERSION,
    ENGINE_ID as QSERIES_OPPORTUNITY_AUTHORIZATION_ENGINE_ID,
    READ_ONLY as QSERIES_OPPORTUNITY_AUTHORIZATION_READ_ONLY,
    EXECUTION_ALLOWED as QSERIES_OPPORTUNITY_AUTHORIZATION_EXECUTION_ALLOWED,
    QSERIES_OWNED,
    OpportunityAuthorizationStatus,
    OpportunityAuthorizationLimits,
    OpportunityAuthorizationDecision,
    OpportunityAuthorizationCheck,
    QSeriesOpportunityAuthorizationResult,
    authorize_oos_opportunities,
    validate_qseries_opportunity_authorization_result,
    assert_qseries_opportunity_authorization_read_only,
)
'''

EXPORT_NAMES = (
    "QSERIES_OPPORTUNITY_AUTHORIZATION_SCHEMA_VERSION",
    "QSERIES_OPPORTUNITY_AUTHORIZATION_ENGINE_ID",
    "QSERIES_OPPORTUNITY_AUTHORIZATION_READ_ONLY",
    "QSERIES_OPPORTUNITY_AUTHORIZATION_EXECUTION_ALLOWED",
    "QSERIES_OWNED",
    "OpportunityAuthorizationStatus",
    "OpportunityAuthorizationLimits",
    "OpportunityAuthorizationDecision",
    "OpportunityAuthorizationCheck",
    "QSeriesOpportunityAuthorizationResult",
    "authorize_oos_opportunities",
    "validate_qseries_opportunity_authorization_result",
    "assert_qseries_opportunity_authorization_read_only",
)


def _write_if_changed(path: Path, content: str) -> bool:
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def _update_init() -> bool:
    existing = INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
    updated = existing
    if "from .qseries_opportunity_authorization_gate import" not in updated:
        updated = updated.rstrip() + "\n" + EXPORT_BLOCK
    missing = [name for name in EXPORT_NAMES if f'    "{name}",' not in updated]
    if missing and "__all__ = [" in updated:
        lines = "".join(f'    "{name}",\n' for name in missing)
        updated = updated.replace("__all__ = [", "__all__ = [\n" + lines, 1)
    return _write_if_changed(INIT_PATH, updated)


def main() -> None:
    INTEGRATION.mkdir(parents=True, exist_ok=True)
    module_changed = _write_if_changed(MODULE_PATH, MODULE_CODE)
    test_changed = _write_if_changed(TEST_PATH, TEST_CODE)
    init_changed = _update_init()
    print("========================================")
    print(" INT-012 INSTALLER")
    print(" Q Series Opportunity Authorization Gate")
    print("========================================")
    print(f"[OK] Module: {MODULE_PATH} changed={module_changed}")
    print(f"[OK] Test: {TEST_PATH} changed={test_changed}")
    print(f"[OK] Exports: {INIT_PATH} changed={init_changed}")
    print()
    print("[DONE] INT-012 installed")
    print()
    print("Run:")
    print("py test_int_012_qseries_opportunity_authorization_gate.py")


if __name__ == "__main__":
    main()
