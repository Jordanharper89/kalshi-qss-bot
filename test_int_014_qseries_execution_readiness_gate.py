from dataclasses import FrozenInstanceError
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from qseries_v2.integration import review_execution_readiness as exported_review_readiness
from qseries_v2.integration.qseries_execution_intake_record import (
    QSeriesExecutionIntakeResult,
    build_qseries_execution_intake_records,
)
from qseries_v2.integration.qseries_execution_readiness_gate import (
    ENGINE_ID,
    EXECUTION_ALLOWED,
    FINAL_EXECUTION_GATE_REQUIRED,
    READ_ONLY,
    SCHEMA_VERSION,
    ExecutionReadinessStatus,
    QSeriesExecutionReadinessResult,
    review_execution_readiness,
    validate_qseries_execution_readiness_result,
)
from qseries_v2.integration.qseries_opportunity_authorization_gate import authorize_oos_opportunities
from qseries_v2.oracle_intelligence.opportunity_operating_system import run_opportunity_subsystem_integration_gate
from qseries_v2.oracle_intelligence.universal_market_model import UniversalMarketFactory
from qseries_v2.oracle_intelligence.universal_opportunity_model import (
    OpportunityExecutionProfile,
    OpportunityTimeWindow,
    UniversalOpportunityFactory,
)


ROOT = Path(__file__).resolve().parent
OBSERVED_AT = "2026-07-10T23:00:00+00:00"


def _market(market_id="KXINT014-YES"):
    return UniversalMarketFactory.from_prediction_market(
        venue_id="kalshi",
        venue_name="Kalshi",
        market_id=market_id,
        title=f"Prediction market {market_id}",
        bid=0.52,
        ask=0.55,
        liquidity=30000,
    )


def _opportunity(market_id="KXINT014-YES", edge=0.12, confidence=0.84, risk=0.25):
    return UniversalOpportunityFactory.prediction_market_scalp(
        market=_market(market_id),
        fair_value=0.55 + edge,
        market_price=0.55,
        confidence=confidence,
        explanation=f"Q Series readiness fixture for {market_id}.",
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
        _opportunity("KXINT014-A", edge=0.08, confidence=0.78, risk=0.22),
        _opportunity("KXINT014-B", edge=0.16, confidence=0.90, risk=0.18),
    )


def _mixed_opportunities():
    return (
        _opportunity("KXINT014-AUTH", edge=0.10, confidence=0.82, risk=0.20),
        _opportunity("KXINT014-LOWCONF", edge=0.10, confidence=0.42, risk=0.20),
        _opportunity("KXINT014-HIGHRISK", edge=0.10, confidence=0.82, risk=0.91),
    )


def _authorization_result(opportunities):
    oos_result = run_opportunity_subsystem_integration_gate(opportunities, observed_at=OBSERVED_AT)
    return authorize_oos_opportunities(opportunities, oos_result=oos_result, observed_at=OBSERVED_AT)


def _intake_result(opportunities=None):
    opportunities = opportunities or _authorized_opportunities()
    return build_qseries_execution_intake_records(
        authorization_result=_authorization_result(opportunities),
        observed_at=OBSERVED_AT,
    )


def test_int_014_accepts_valid_intake_records_into_next_boundary():
    result = review_execution_readiness(intake_result=_intake_result(), observed_at=OBSERVED_AT)

    assert isinstance(result, QSeriesExecutionReadinessResult)
    assert result.schema_version == "INT-014"
    assert result.engine_id == "INT-014"
    assert result.status == "passed"
    assert result.ready_count == 2
    assert result.rejected_count == 0
    assert all(record.status == ExecutionReadinessStatus.READY_FOR_EXECUTION_GATE for record in result.ready_records)
    assert result.read_only is True
    assert result.execution_allowed is False
    assert result.final_execution_gate_required is True


def test_int_014_rejects_malformed_or_unauthorized_intake_records():
    intake = _intake_result(_mixed_opportunities())
    malformed = QSeriesExecutionIntakeResult(
        intake.schema_version,
        intake.engine_id,
        intake.observed_at,
        intake.status,
        intake.records + intake.rejected_decisions,
        tuple(),
        intake.checks,
        intake.pass_count,
        intake.fail_count,
        intake.accepted_count,
        intake.rejected_count,
        intake.intake_hash,
        intake.read_only,
        intake.execution_allowed,
        intake.qseries_owned,
        intake.execution_gate_required,
        intake.explanation,
        intake.telemetry,
    )

    result = review_execution_readiness(intake_result=malformed, observed_at=OBSERVED_AT)

    assert result.status == "failed"
    assert result.ready_count == 1
    assert result.rejected_count == 2
    reasons = {reason for record in result.rejected_records for reason in record.reasons}
    assert "intake_record_not_accepted" in reasons


def test_int_014_rejects_failed_intake_result():
    intake = _intake_result()
    failed_intake = QSeriesExecutionIntakeResult(
        intake.schema_version,
        intake.engine_id,
        intake.observed_at,
        "failed",
        intake.records,
        intake.rejected_decisions,
        intake.checks,
        intake.pass_count,
        1,
        intake.accepted_count,
        intake.rejected_count,
        intake.intake_hash,
        intake.read_only,
        intake.execution_allowed,
        intake.qseries_owned,
        intake.execution_gate_required,
        intake.explanation,
        intake.telemetry,
    )

    result = review_execution_readiness(intake_result=failed_intake, observed_at=OBSERVED_AT)
    check_map = {check.check_id: check for check in result.checks}

    assert result.status == "failed"
    assert result.ready_records == tuple()
    assert check_map["int013_intake_valid"].passed is False


def test_int_014_deterministic_ids_and_hashes():
    intake = _intake_result()
    first = review_execution_readiness(intake_result=intake, observed_at=OBSERVED_AT)
    second = review_execution_readiness(intake_result=intake, observed_at=OBSERVED_AT)

    assert first.readiness_hash == second.readiness_hash
    assert [record.readiness_id for record in first.ready_records] == [record.readiness_id for record in second.ready_records]
    assert first.to_dict() == second.to_dict()
    assert first.verify_readiness_hash() is True


def test_int_014_caller_timestamp_behavior():
    intake = _intake_result()
    first = review_execution_readiness(intake_result=intake, observed_at="2026-07-10T23:00:00+00:00")
    second = review_execution_readiness(intake_result=intake, observed_at="2026-07-10T23:05:00+00:00")

    assert first.observed_at != second.observed_at
    assert first.ready_records[0].readiness_id != second.ready_records[0].readiness_id
    try:
        review_execution_readiness(intake_result=intake, observed_at="")
        raise AssertionError("observed_at must be caller supplied.")
    except ValueError:
        pass


def test_int_014_frozen_and_json_serializable():
    result = review_execution_readiness(intake_result=_intake_result(), observed_at=OBSERVED_AT)

    try:
        result.status = "failed"
        raise AssertionError("QSeriesExecutionReadinessResult must be frozen.")
    except FrozenInstanceError:
        pass

    encoded = json.dumps(result.to_dict(), sort_keys=True)
    assert '"schema_version": "INT-014"' in encoded


def test_int_014_no_live_execution_occurs():
    result = review_execution_readiness(intake_result=_intake_result(), observed_at=OBSERVED_AT)
    telemetry = dict(result.telemetry)

    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert FINAL_EXECUTION_GATE_REQUIRED is True
    assert result.read_only is True
    assert result.execution_allowed is False
    assert telemetry["orders_placed"] is False
    assert telemetry["exchange_calls"] is False
    assert telemetry["funds_moved"] is False
    assert telemetry["portfolio_mutation"] is False


def test_int_014_no_filesystem_or_database_writes():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        before = sorted(path.relative_to(root) for path in root.rglob("*"))
        result = review_execution_readiness(intake_result=_intake_result(), observed_at=OBSERVED_AT)
        after = sorted(path.relative_to(root) for path in root.rglob("*"))

    assert before == after
    assert dict(result.telemetry)["files_written"] is False
    assert dict(result.telemetry)["databases_written"] is False


def test_int_014_validation_and_package_export():
    result = exported_review_readiness(intake_result=_intake_result(), observed_at=OBSERVED_AT)
    validation = validate_qseries_execution_readiness_result(result)

    assert validation["passed"] is True
    assert all(validation["checks"].values())
    assert SCHEMA_VERSION == "INT-014"
    assert ENGINE_ID == "INT-014"


def test_int_014_installer_is_idempotent():
    tracked = (
        ROOT / "build_int_014_qseries_execution_readiness_gate.py",
        ROOT / "qseries_v2" / "integration" / "qseries_execution_readiness_gate.py",
        ROOT / "test_int_014_qseries_execution_readiness_gate.py",
        ROOT / "qseries_v2" / "integration" / "__init__.py",
    )
    before = {path: path.read_text(encoding="utf-8") for path in tracked}
    subprocess.run(
        [sys.executable, str(ROOT / "build_int_014_qseries_execution_readiness_gate.py")],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    after = {path: path.read_text(encoding="utf-8") for path in tracked}
    assert before == after


if __name__ == "__main__":
    test_int_014_accepts_valid_intake_records_into_next_boundary()
    test_int_014_rejects_malformed_or_unauthorized_intake_records()
    test_int_014_rejects_failed_intake_result()
    test_int_014_deterministic_ids_and_hashes()
    test_int_014_caller_timestamp_behavior()
    test_int_014_frozen_and_json_serializable()
    test_int_014_no_live_execution_occurs()
    test_int_014_no_filesystem_or_database_writes()
    test_int_014_validation_and_package_export()
    test_int_014_installer_is_idempotent()

    readiness = review_execution_readiness(intake_result=_intake_result(), observed_at=OBSERVED_AT)
    print("[PASS] INT-014 Q Series Execution Readiness Gate")
    print(
        {
            "schema_version": readiness.schema_version,
            "engine_id": readiness.engine_id,
            "status": readiness.status,
            "ready_count": readiness.ready_count,
            "rejected_count": readiness.rejected_count,
            "read_only": readiness.read_only,
            "execution_allowed": readiness.execution_allowed,
            "final_execution_gate_required": readiness.final_execution_gate_required,
        }
    )
