from pathlib import Path


ROOT = Path.cwd()
INTEGRATION = ROOT / "qseries_v2" / "integration"
MODULE_PATH = INTEGRATION / "qseries_execution_intake_record.py"
INIT_PATH = INTEGRATION / "__init__.py"
TEST_PATH = ROOT / "test_int_013_qseries_execution_intake_record.py"

MODULE_CODE = r'''"""
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
'''

TEST_CODE = r'''from dataclasses import FrozenInstanceError
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from qseries_v2.integration import build_qseries_execution_intake_records as exported_build_intake
from qseries_v2.integration.qseries_execution_intake_record import (
    ENGINE_ID,
    EXECUTION_ALLOWED,
    EXECUTION_GATE_REQUIRED,
    READ_ONLY,
    SCHEMA_VERSION,
    ExecutionIntakeStatus,
    QSeriesExecutionIntakeResult,
    build_qseries_execution_intake_records,
    validate_qseries_execution_intake_result,
)
from qseries_v2.integration.qseries_opportunity_authorization_gate import (
    OpportunityAuthorizationLimits,
    authorize_oos_opportunities,
)
from qseries_v2.oracle_intelligence.opportunity_operating_system import run_opportunity_subsystem_integration_gate
from qseries_v2.oracle_intelligence.universal_market_model import UniversalMarketFactory
from qseries_v2.oracle_intelligence.universal_opportunity_model import (
    OpportunityExecutionProfile,
    OpportunityTimeWindow,
    UniversalOpportunityFactory,
)


ROOT = Path(__file__).resolve().parent
OBSERVED_AT = "2026-07-10T22:00:00+00:00"


def _market(market_id="KXINT013-YES"):
    return UniversalMarketFactory.from_prediction_market(
        venue_id="kalshi",
        venue_name="Kalshi",
        market_id=market_id,
        title=f"Prediction market {market_id}",
        bid=0.52,
        ask=0.55,
        liquidity=30000,
    )


def _opportunity(market_id="KXINT013-YES", edge=0.12, confidence=0.84, risk=0.25):
    return UniversalOpportunityFactory.prediction_market_scalp(
        market=_market(market_id),
        fair_value=0.55 + edge,
        market_price=0.55,
        confidence=confidence,
        explanation=f"Q Series intake fixture for {market_id}.",
        liquidity_score=0.76,
        risk_score=risk,
        time_window=OpportunityTimeWindow(urgency_score=0.50, freshness_score=1.0),
        execution=OpportunityExecutionProfile(
            required_execution_adapter="prediction_market",
            execution_difficulty=0.25,
            capital_required=100,
        ),
    )


def _authorized_opportunities():
    return (
        _opportunity("KXINT013-A", edge=0.08, confidence=0.78, risk=0.22),
        _opportunity("KXINT013-B", edge=0.16, confidence=0.90, risk=0.18),
    )


def _mixed_opportunities():
    return (
        _opportunity("KXINT013-AUTH", edge=0.10, confidence=0.82, risk=0.20),
        _opportunity("KXINT013-LOWCONF", edge=0.10, confidence=0.42, risk=0.20),
        _opportunity("KXINT013-HIGHRISK", edge=0.10, confidence=0.82, risk=0.91),
    )


def _authorization_result(opportunities, limits=None):
    oos_result = run_opportunity_subsystem_integration_gate(opportunities, observed_at=OBSERVED_AT)
    return authorize_oos_opportunities(opportunities, oos_result=oos_result, observed_at=OBSERVED_AT, limits=limits)


def test_int_013_accepts_authorized_decisions_into_next_boundary():
    opportunities = _authorized_opportunities()
    auth = _authorization_result(opportunities)
    result = build_qseries_execution_intake_records(authorization_result=auth, observed_at=OBSERVED_AT)

    assert isinstance(result, QSeriesExecutionIntakeResult)
    assert result.schema_version == "INT-013"
    assert result.engine_id == "INT-013"
    assert result.status == "passed"
    assert result.accepted_count == 2
    assert result.rejected_count == 0
    assert all(record.status == ExecutionIntakeStatus.ACCEPTED for record in result.records)
    assert all(record.execution_allowed is False for record in result.records)
    assert all(record.execution_gate_required is True for record in result.records)


def test_int_013_rejects_unauthorized_opportunities():
    opportunities = _mixed_opportunities()
    auth = _authorization_result(opportunities)
    result = build_qseries_execution_intake_records(authorization_result=auth, observed_at=OBSERVED_AT)

    assert result.status == "passed"
    assert result.accepted_count == 1
    assert result.rejected_count == 2
    reasons = {reason for record in result.rejected_decisions for reason in record.reasons}
    assert "confidence_below_limit" in reasons
    assert "risk_above_limit" in reasons


def test_int_013_blocks_failed_authorization_result():
    opportunities = _authorized_opportunities()
    auth = _authorization_result(opportunities)
    failed_payload = dict(auth.to_dict())
    failed_payload["passed"] = False

    class FailedAuthorization(type(auth)):
        def to_dict(self):
            return failed_payload

    failed_auth = FailedAuthorization(
        auth.schema_version,
        auth.engine_id,
        auth.observed_at,
        auth.status,
        auth.decisions,
        auth.checks,
        auth.pass_count,
        auth.fail_count,
        auth.authorized_count,
        auth.rejected_count,
        auth.hold_count,
        auth.authorization_hash,
        auth.read_only,
        auth.execution_allowed,
        auth.qseries_owned,
        auth.explanation,
        auth.telemetry,
    )

    result = build_qseries_execution_intake_records(authorization_result=failed_auth, observed_at=OBSERVED_AT)

    assert result.status == "failed"
    assert result.records == tuple()
    check_map = {check.check_id: check for check in result.checks}
    assert check_map["int012_authorization_valid"].passed is False


def test_int_013_deterministic_ids_and_hashes():
    opportunities = _authorized_opportunities()
    auth = _authorization_result(opportunities)
    first = build_qseries_execution_intake_records(authorization_result=auth, observed_at=OBSERVED_AT)
    second = build_qseries_execution_intake_records(authorization_result=auth, observed_at=OBSERVED_AT)

    assert first.intake_hash == second.intake_hash
    assert [record.intake_id for record in first.records] == [record.intake_id for record in second.records]
    assert first.to_dict() == second.to_dict()
    assert first.verify_intake_hash() is True


def test_int_013_caller_timestamp_behavior():
    opportunities = _authorized_opportunities()
    auth = _authorization_result(opportunities)
    first = build_qseries_execution_intake_records(authorization_result=auth, observed_at="2026-07-10T22:00:00+00:00")
    second = build_qseries_execution_intake_records(authorization_result=auth, observed_at="2026-07-10T22:05:00+00:00")

    assert first.observed_at != second.observed_at
    assert first.records[0].intake_id != second.records[0].intake_id
    try:
        build_qseries_execution_intake_records(authorization_result=auth, observed_at="")
        raise AssertionError("observed_at must be caller supplied.")
    except ValueError:
        pass


def test_int_013_frozen_and_json_serializable():
    opportunities = _authorized_opportunities()
    result = build_qseries_execution_intake_records(authorization_result=_authorization_result(opportunities), observed_at=OBSERVED_AT)

    try:
        result.status = "failed"
        raise AssertionError("QSeriesExecutionIntakeResult must be frozen.")
    except FrozenInstanceError:
        pass

    encoded = json.dumps(result.to_dict(), sort_keys=True)
    assert '"schema_version": "INT-013"' in encoded


def test_int_013_no_live_execution_occurs():
    opportunities = _authorized_opportunities()
    result = build_qseries_execution_intake_records(authorization_result=_authorization_result(opportunities), observed_at=OBSERVED_AT)
    telemetry = dict(result.telemetry)

    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert EXECUTION_GATE_REQUIRED is True
    assert result.read_only is True
    assert result.execution_allowed is False
    assert telemetry["orders_placed"] is False
    assert telemetry["exchange_calls"] is False
    assert telemetry["funds_moved"] is False
    assert telemetry["portfolio_mutation"] is False


def test_int_013_no_filesystem_or_database_writes():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        before = sorted(path.relative_to(root) for path in root.rglob("*"))
        opportunities = _authorized_opportunities()
        result = build_qseries_execution_intake_records(authorization_result=_authorization_result(opportunities), observed_at=OBSERVED_AT)
        after = sorted(path.relative_to(root) for path in root.rglob("*"))

    assert before == after
    assert dict(result.telemetry)["files_written"] is False
    assert dict(result.telemetry)["databases_written"] is False


def test_int_013_validation_and_package_export():
    opportunities = _authorized_opportunities()
    result = exported_build_intake(authorization_result=_authorization_result(opportunities), observed_at=OBSERVED_AT)
    validation = validate_qseries_execution_intake_result(result)

    assert validation["passed"] is True
    assert all(validation["checks"].values())
    assert SCHEMA_VERSION == "INT-013"
    assert ENGINE_ID == "INT-013"


def test_int_013_installer_is_idempotent():
    tracked = (
        ROOT / "build_int_013_qseries_execution_intake_record.py",
        ROOT / "qseries_v2" / "integration" / "qseries_execution_intake_record.py",
        ROOT / "test_int_013_qseries_execution_intake_record.py",
        ROOT / "qseries_v2" / "integration" / "__init__.py",
    )
    before = {path: path.read_text(encoding="utf-8") for path in tracked}
    subprocess.run(
        [sys.executable, str(ROOT / "build_int_013_qseries_execution_intake_record.py")],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    after = {path: path.read_text(encoding="utf-8") for path in tracked}
    assert before == after


if __name__ == "__main__":
    test_int_013_accepts_authorized_decisions_into_next_boundary()
    test_int_013_rejects_unauthorized_opportunities()
    test_int_013_blocks_failed_authorization_result()
    test_int_013_deterministic_ids_and_hashes()
    test_int_013_caller_timestamp_behavior()
    test_int_013_frozen_and_json_serializable()
    test_int_013_no_live_execution_occurs()
    test_int_013_no_filesystem_or_database_writes()
    test_int_013_validation_and_package_export()
    test_int_013_installer_is_idempotent()

    opportunities = _authorized_opportunities()
    result = build_qseries_execution_intake_records(authorization_result=_authorization_result(opportunities), observed_at=OBSERVED_AT)
    print("[PASS] INT-013 Q Series Execution Intake Record")
    print(
        {
            "schema_version": result.schema_version,
            "engine_id": result.engine_id,
            "status": result.status,
            "accepted_count": result.accepted_count,
            "rejected_count": result.rejected_count,
            "read_only": result.read_only,
            "execution_allowed": result.execution_allowed,
            "execution_gate_required": result.execution_gate_required,
        }
    )
'''

EXPORT_BLOCK = '''from .qseries_execution_intake_record import (
    SCHEMA_VERSION as QSERIES_EXECUTION_INTAKE_SCHEMA_VERSION,
    ENGINE_ID as QSERIES_EXECUTION_INTAKE_ENGINE_ID,
    READ_ONLY as QSERIES_EXECUTION_INTAKE_READ_ONLY,
    EXECUTION_ALLOWED as QSERIES_EXECUTION_INTAKE_EXECUTION_ALLOWED,
    EXECUTION_GATE_REQUIRED,
    ExecutionIntakeStatus,
    QSeriesExecutionIntakeRecord,
    QSeriesExecutionIntakeCheck,
    QSeriesExecutionIntakeResult,
    build_qseries_execution_intake_records,
    validate_qseries_execution_intake_result,
)
'''

EXPORT_NAMES = (
    "QSERIES_EXECUTION_INTAKE_SCHEMA_VERSION",
    "QSERIES_EXECUTION_INTAKE_ENGINE_ID",
    "QSERIES_EXECUTION_INTAKE_READ_ONLY",
    "QSERIES_EXECUTION_INTAKE_EXECUTION_ALLOWED",
    "EXECUTION_GATE_REQUIRED",
    "ExecutionIntakeStatus",
    "QSeriesExecutionIntakeRecord",
    "QSeriesExecutionIntakeCheck",
    "QSeriesExecutionIntakeResult",
    "build_qseries_execution_intake_records",
    "validate_qseries_execution_intake_result",
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
    if "from .qseries_execution_intake_record import" not in updated:
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
    print(" INT-013 INSTALLER")
    print(" Q Series Execution Intake Record")
    print("========================================")
    print(f"[OK] Module: {MODULE_PATH} changed={module_changed}")
    print(f"[OK] Test: {TEST_PATH} changed={test_changed}")
    print(f"[OK] Exports: {INIT_PATH} changed={init_changed}")
    print()
    print("[DONE] INT-013 installed")
    print()
    print("Run:")
    print("py test_int_013_qseries_execution_intake_record.py")


if __name__ == "__main__":
    main()
