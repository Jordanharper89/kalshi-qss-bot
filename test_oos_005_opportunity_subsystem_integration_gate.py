from dataclasses import FrozenInstanceError
import json
import subprocess
import sys
from pathlib import Path

from qseries_v2.oracle_intelligence.opportunity_operating_system import (
    EXPECTED_MODULES,
    OpportunitySubsystemIntegrationResult,
    run_opportunity_subsystem_integration_gate,
)
from qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_subsystem_integration_gate import (
    ENGINE_ID,
    EXECUTION_ALLOWED,
    READ_ONLY,
    SCHEMA_VERSION,
    assert_opportunity_subsystem_read_only,
    validate_opportunity_subsystem_integration_gate,
)
from qseries_v2.oracle_intelligence.universal_market_model import UniversalMarketFactory
from qseries_v2.oracle_intelligence.universal_opportunity_model import (
    OpportunityExecutionProfile,
    OpportunityTimeWindow,
    UniversalOpportunityFactory,
)


ROOT = Path(__file__).resolve().parent
OBSERVED_AT = "2026-07-10T20:00:00+00:00"


def _market(market_id="KXOOS-YES"):
    return UniversalMarketFactory.from_prediction_market(
        venue_id="kalshi",
        venue_name="Kalshi",
        market_id=market_id,
        title=f"Prediction market {market_id}",
        bid=0.52,
        ask=0.55,
        liquidity=30000,
    )


def _opportunity(market_id="KXOOS-YES", edge=0.12, confidence=0.84):
    return UniversalOpportunityFactory.prediction_market_scalp(
        market=_market(market_id),
        fair_value=0.55 + edge,
        market_price=0.55,
        confidence=confidence,
        explanation=f"Oracle fair value gap for {market_id}.",
        liquidity_score=0.76,
        risk_score=0.31,
        time_window=OpportunityTimeWindow(urgency_score=0.50, freshness_score=1.0),
        execution=OpportunityExecutionProfile(
            required_execution_adapter="prediction_market",
            execution_difficulty=0.25,
            capital_required=100,
        ),
    )


def _opportunities():
    return (
        _opportunity("KXOOS-A", edge=0.08, confidence=0.78),
        _opportunity("KXOOS-B", edge=0.16, confidence=0.90),
        _opportunity("KXOOS-C", edge=0.12, confidence=0.84),
    )


class InvalidOpportunity:
    read_only = True

    def fingerprint(self):
        return "invalid-fixture"

    def to_dict(self):
        return {"opportunity_id": "invalid-fixture", "read_only": True}


def test_oos_005_module_coverage():
    result = run_opportunity_subsystem_integration_gate(_opportunities(), observed_at=OBSERVED_AT)
    assert SCHEMA_VERSION == "OOS-005"
    assert ENGINE_ID == "OOS-005"
    assert result.modules == ("OOS-001", "OOS-002", "OOS-003", "OOS-004", "OOS-005")
    assert EXPECTED_MODULES == result.modules


def test_oos_005_valid_fixtures_pass_all_checks():
    result = run_opportunity_subsystem_integration_gate(_opportunities(), observed_at=OBSERVED_AT, source="unit_test")
    assert isinstance(result, OpportunitySubsystemIntegrationResult)
    assert result.passed is True
    assert result.fail_count == 0
    assert result.pass_count == len(result.checks)
    assert all(check.passed for check in result.checks)
    assert result.verify_integration_hash() is True


def test_oos_005_invalid_fixture_surfaces_validation_failure():
    result = run_opportunity_subsystem_integration_gate([InvalidOpportunity()], observed_at=OBSERVED_AT)
    assert result.passed is False
    assert result.fail_count >= 1
    check_map = {check.check_id: check for check in result.checks}
    assert check_map["oos_004_validation"].passed is False
    assert check_map["pipeline_handoff"].passed is False
    details = dict(check_map["oos_004_validation"].details)
    assert details["validation_failures"] > 0


def test_oos_005_deterministic_hash():
    opportunities = _opportunities()
    first = run_opportunity_subsystem_integration_gate(opportunities, observed_at=OBSERVED_AT)
    second = run_opportunity_subsystem_integration_gate(opportunities, observed_at=OBSERVED_AT)
    assert first.integration_hash == second.integration_hash
    assert first.to_dict() == second.to_dict()


def test_oos_005_order_independent_hash():
    opportunities = _opportunities()
    first = run_opportunity_subsystem_integration_gate(opportunities, observed_at=OBSERVED_AT)
    second = run_opportunity_subsystem_integration_gate(tuple(reversed(opportunities)), observed_at=OBSERVED_AT)
    assert first.integration_hash == second.integration_hash
    assert first.telemetry == second.telemetry


def test_oos_005_frozen_result():
    result = run_opportunity_subsystem_integration_gate(_opportunities(), observed_at=OBSERVED_AT)
    try:
        result.passed = False
        raise AssertionError("OpportunitySubsystemIntegrationResult must be frozen.")
    except FrozenInstanceError:
        pass


def test_oos_005_read_only_execution_disabled():
    result = run_opportunity_subsystem_integration_gate(_opportunities(), observed_at=OBSERVED_AT)
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert result.read_only is True
    assert result.execution_allowed is False
    assert assert_opportunity_subsystem_read_only(result) is True


def test_oos_005_no_filesystem_or_database_writes(tmp_path):
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    result = run_opportunity_subsystem_integration_gate(_opportunities(), observed_at=OBSERVED_AT)
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert before == after
    assert dict(result.telemetry)["files_written"] is False
    assert dict(result.telemetry)["databases_written"] is False
    assert dict(result.telemetry)["runtime_state_written"] is False


def test_oos_005_json_serializable():
    result = run_opportunity_subsystem_integration_gate(_opportunities(), observed_at=OBSERVED_AT)
    encoded = json.dumps(result.to_dict(), sort_keys=True)
    assert '"schema_version": "OOS-005"' in encoded


def test_oos_005_validation_helper():
    result = run_opportunity_subsystem_integration_gate(_opportunities(), observed_at=OBSERVED_AT)
    validation = validate_opportunity_subsystem_integration_gate(result)
    assert validation["passed"] is True
    assert all(validation["checks"].values())


def test_oos_005_package_export_works():
    from qseries_v2.oracle_intelligence.opportunity_operating_system import (
        ENGINE_ID as exported_engine_id,
        run_opportunity_subsystem_integration_gate as exported_gate,
    )
    assert exported_engine_id == "OOS-005"
    result = exported_gate(_opportunities(), observed_at=OBSERVED_AT)
    assert result.schema_version == "OOS-005"


def test_oos_005_installer_is_idempotent():
    tracked = (
        ROOT / "build_oos_005_opportunity_subsystem_integration_gate.py",
        ROOT / "qseries_v2" / "oracle_intelligence" / "opportunity_operating_system" / "opportunity_subsystem_integration_gate.py",
        ROOT / "test_oos_005_opportunity_subsystem_integration_gate.py",
        ROOT / "qseries_v2" / "oracle_intelligence" / "opportunity_operating_system" / "__init__.py",
    )
    before = {path: path.read_text(encoding="utf-8") for path in tracked}
    subprocess.run(
        [sys.executable, str(ROOT / "build_oos_005_opportunity_subsystem_integration_gate.py")],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    after = {path: path.read_text(encoding="utf-8") for path in tracked}
    assert before == after


def test_oos_005_requires_caller_observed_at():
    try:
        run_opportunity_subsystem_integration_gate(_opportunities(), observed_at="")
        raise AssertionError("observed_at must be caller supplied.")
    except ValueError:
        pass


if __name__ == "__main__":
    test_oos_005_module_coverage()
    test_oos_005_valid_fixtures_pass_all_checks()
    test_oos_005_invalid_fixture_surfaces_validation_failure()
    test_oos_005_deterministic_hash()
    test_oos_005_order_independent_hash()
    test_oos_005_frozen_result()
    test_oos_005_read_only_execution_disabled()
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        test_oos_005_no_filesystem_or_database_writes(Path(tmp))
    test_oos_005_json_serializable()
    test_oos_005_validation_helper()
    test_oos_005_package_export_works()
    test_oos_005_installer_is_idempotent()
    test_oos_005_requires_caller_observed_at()

    result = run_opportunity_subsystem_integration_gate(_opportunities(), observed_at=OBSERVED_AT)
    print("[PASS] OOS-005 Opportunity Subsystem Integration Gate")
    print(
        {
            "schema_version": result.schema_version,
            "engine_id": result.engine_id,
            "modules": list(result.modules),
            "pass_count": result.pass_count,
            "fail_count": result.fail_count,
            "passed": result.passed,
            "read_only": result.read_only,
            "execution_allowed": result.execution_allowed,
        }
    )


