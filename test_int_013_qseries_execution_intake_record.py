from dataclasses import FrozenInstanceError
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
