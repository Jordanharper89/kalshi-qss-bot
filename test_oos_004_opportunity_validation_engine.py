from dataclasses import FrozenInstanceError

from qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_validation_engine import (
    OOS_VALIDATION_VERSION,
    ValidationRuleConfig,
    ValidationStatus,
    build_validation_engine,
)
from qseries_v2.oracle_intelligence.universal_market_model import UniversalMarketFactory
from qseries_v2.oracle_intelligence.universal_opportunity_model import (
    OpportunityExecutionProfile,
    OpportunityTimeWindow,
    UniversalOpportunityFactory,
)


def _market():
    return UniversalMarketFactory.from_prediction_market(
        venue_id="kalshi",
        venue_name="Kalshi",
        market_id="KXBTC-YES",
        title="Will BTC close above 100k?",
        bid=0.52,
        ask=0.55,
        liquidity=30000,
    )


def _valid_opportunity():
    return UniversalOpportunityFactory.prediction_market_scalp(
        market=_market(),
        fair_value=0.67,
        market_price=0.55,
        confidence=0.84,
        explanation="Oracle fair value is above market ask.",
        liquidity_score=0.76,
        risk_score=0.31,
        time_window=OpportunityTimeWindow(urgency_score=0.5, freshness_score=1.0),
        execution=OpportunityExecutionProfile(
            required_execution_adapter="prediction_market",
            execution_difficulty=0.25,
            capital_required=100,
        ),
    )


def test_oos_004_valid_opportunity_passes():
    engine = build_validation_engine()
    report = engine.validate(_valid_opportunity())

    assert report.schema_version == OOS_VALIDATION_VERSION
    assert report.read_only is True
    assert report.status in {ValidationStatus.PASSED, ValidationStatus.WARNING}
    assert report.failed_checks == 0
    assert report.is_accepted() is True
    assert report.fingerprint is not None


def test_oos_004_non_read_only_fails():
    class BadOpportunity:
        read_only = False
        opportunity_id = "bad_1"
        market_id = "bad_market"
        market_type = "bad_type"
        venue_id = "bad_venue"
        venue_name = "Bad Venue"
        opportunity_type = "bad"
        direction = "BUY"
        expected_value = 1
        expected_edge = 0.1
        confidence = 0.5
        time_window = object()
        execution = object()
        explanation = "bad"

        def fingerprint(self):
            return "bad"

        def to_dict(self):
            return {}

    engine = build_validation_engine()
    report = engine.validate(BadOpportunity())

    assert report.status == ValidationStatus.FAILED
    assert report.failed_checks >= 1
    assert report.is_accepted() is False


def test_oos_004_missing_required_fields_fail():
    class IncompleteOpportunity:
        read_only = True

        def fingerprint(self):
            return "incomplete"

        def to_dict(self):
            return {}

    engine = build_validation_engine()
    report = engine.validate(IncompleteOpportunity())

    assert report.status == ValidationStatus.FAILED
    assert report.failed_checks > 5
    assert report.is_accepted() is False


def test_oos_004_business_rules_fail_low_confidence_and_zero_edge():
    opportunity = UniversalOpportunityFactory.prediction_market_scalp(
        market=_market(),
        fair_value=0.55,
        market_price=0.55,
        confidence=0.0,
        explanation="No edge.",
        liquidity_score=0.5,
        risk_score=0.2,
    )

    engine = build_validation_engine()
    report = engine.validate(opportunity)

    assert report.status == ValidationStatus.FAILED
    assert report.failed_checks >= 2
    assert report.is_accepted() is False


def test_oos_004_warning_for_high_risk_execution_and_flags():
    market = UniversalMarketFactory.from_solana_token_launch(
        token_mint="Mint111",
        token_symbol="MEME",
        liquidity=1200,
    )

    opportunity = UniversalOpportunityFactory.solana_token_snipe(
        market=market,
        expected_multiple=2.5,
        confidence=0.62,
        explanation="High-risk launch candidate.",
        execution=OpportunityExecutionProfile(
            required_execution_adapter="solana_wallet",
            execution_difficulty=0.95,
            capital_required=2500,
        ),
    )

    engine = build_validation_engine(
        ValidationRuleConfig(
            max_capital_required_warning=1000,
            require_evidence_warning=True,
        )
    )

    report = engine.validate(opportunity)

    assert report.failed_checks == 0
    assert report.warning_count >= 3
    assert report.status == ValidationStatus.WARNING
    assert report.is_accepted() is True


def test_oos_004_supported_type_config():
    opportunity = _valid_opportunity()
    engine = build_validation_engine(
        ValidationRuleConfig(
            supported_opportunity_types=["arbitrage_spread"]
        )
    )

    report = engine.validate(opportunity)

    assert report.status == ValidationStatus.FAILED
    assert any(check.check_id == "business.supported_opportunity_type" for check in report.checks)


def test_oos_004_validate_many_and_serialization():
    engine = build_validation_engine()
    reports = engine.validate_many([_valid_opportunity(), _valid_opportunity()])

    assert len(reports) == 2
    assert all(report.is_accepted() for report in reports)

    data = reports[0].to_dict()

    assert data["schema_version"] == OOS_VALIDATION_VERSION
    assert data["read_only"] is True
    assert "checks" in data
    assert data["opportunity_id"] != "unknown_opportunity"


def test_oos_004_report_immutability():
    report = build_validation_engine().validate(_valid_opportunity())

    try:
        report.status = ValidationStatus.FAILED
        raise AssertionError("Validation report should be immutable.")
    except FrozenInstanceError:
        pass


if __name__ == "__main__":
    test_oos_004_valid_opportunity_passes()
    test_oos_004_non_read_only_fails()
    test_oos_004_missing_required_fields_fail()
    test_oos_004_business_rules_fail_low_confidence_and_zero_edge()
    test_oos_004_warning_for_high_risk_execution_and_flags()
    test_oos_004_supported_type_config()
    test_oos_004_validate_many_and_serialization()
    test_oos_004_report_immutability()

    report = build_validation_engine().validate(_valid_opportunity())

    print("[PASS] OOS-004 Opportunity Validation Engine")
    print(
        {
            "schema_version": report.schema_version,
            "status": report.status.value,
            "passed_checks": report.passed_checks,
            "failed_checks": report.failed_checks,
            "warning_count": report.warning_count,
            "read_only": report.read_only,
        }
    )
