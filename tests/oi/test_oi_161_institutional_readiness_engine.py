from qseries_v2.oracle_intelligence.institutional_readiness_engine import (
    oracle_institutional_readiness_engine,
)


def sample_alpha(status="alpha_integration_ready", critical=0, warnings=0, packets=5):
    return {
        "alpha_integration_id": "alpha-001",
        "alpha_status": status,
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "universal_market_model_ready": True,
        "packet_count": packets,
        "issue_count": critical + warnings,
        "critical_count": critical,
        "warning_count": warnings,
    }


def test_institutional_readiness_ready():
    report = oracle_institutional_readiness_engine.evaluate(sample_alpha())

    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["readiness_status"] in ("institutional_ready", "alpha_ready")
    assert report["readiness_score"] >= 85
    assert report["dimension_count"] == 8


def test_warning_alpha_becomes_alpha_ready_or_review():
    report = oracle_institutional_readiness_engine.evaluate(
        sample_alpha("alpha_integration_ready_with_warnings", critical=0, warnings=2)
    )

    assert report["readiness_status"] in ("alpha_ready", "ready_with_review")
    assert report["source_warning_count"] == 2
    assert report["source_critical_count"] == 0


def test_critical_issue_not_ready():
    report = oracle_institutional_readiness_engine.evaluate(
        sample_alpha("alpha_integration_failed", critical=1, warnings=0)
    )

    assert report["readiness_status"] == "not_ready"
    assert report["source_critical_count"] == 1


def test_execution_contract_failure_not_ready():
    alpha = sample_alpha()
    alpha["execution_allowed"] = True

    report = oracle_institutional_readiness_engine.evaluate(alpha)

    assert report["readiness_status"] == "not_ready"
    assert any(d["dimension"] == "read_only_contract" for d in report["dimensions"])


def test_explain_dimension():
    report = oracle_institutional_readiness_engine.evaluate(sample_alpha())
    explanation = oracle_institutional_readiness_engine.explain_dimension(report, "universal_market_model")

    assert explanation["found"] is True
    assert explanation["read_only"] is True
    assert explanation["execution_allowed"] is False
    assert explanation["dimension_record"]["dimension"] == "universal_market_model"


if __name__ == "__main__":
    test_institutional_readiness_ready()
    test_warning_alpha_becomes_alpha_ready_or_review()
    test_critical_issue_not_ready()
    test_execution_contract_failure_not_ready()
    test_explain_dimension()
    print("[PASS] OI-161 Oracle Institutional Readiness Engine")
