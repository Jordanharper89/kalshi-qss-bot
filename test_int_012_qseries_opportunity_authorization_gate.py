from dataclasses import FrozenInstanceError
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
