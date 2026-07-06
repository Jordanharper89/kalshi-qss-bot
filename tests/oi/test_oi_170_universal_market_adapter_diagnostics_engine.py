from qseries_v2.oracle_intelligence.universal_market_adapter_diagnostics_engine import (
    oracle_universal_market_adapter_diagnostics_engine,
)


def clean_health_report():
    return {
        "adapter_health_report_id": "health-001",
        "health_report_status": "adapter_health_institutional",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "records": [
            {
                "adapter_health_id": "adapter-health-001",
                "adapter_id": "adp.crypto",
                "domain": "CRYPTO",
                "health_score": 100.0,
                "health_status": "institutional_adapter_ready",
                "validation_status": "adapter_packet_valid",
                "issue_count": 0,
                "critical_count": 0,
                "warning_count": 0,
                "institutional_ready": True,
                "safety_status": "safety_confirmed",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            }
        ],
    }


def test_clean_diagnostics():
    diagnostics = oracle_universal_market_adapter_diagnostics_engine.diagnose(clean_health_report())

    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False
    assert diagnostics["execution_owner"] == "Q Series"
    assert diagnostics["diagnostics_status"] == "adapter_diagnostics_clean"
    assert diagnostics["critical_count"] == 0
    assert diagnostics["warning_count"] == 0
    assert diagnostics["info_count"] == 1
    assert diagnostics["findings"][0]["code"] == "adapter_diagnostics_clean"


def test_critical_diagnostics():
    report = clean_health_report()
    record = report["records"][0]
    record["critical_count"] = 1
    record["issue_count"] = 1
    record["health_score"] = 55.0
    record["health_status"] = "adapter_health_critical"
    record["validation_status"] = "adapter_packet_invalid"
    record["institutional_ready"] = False

    diagnostics = oracle_universal_market_adapter_diagnostics_engine.diagnose(report)

    assert diagnostics["diagnostics_status"] == "adapter_diagnostics_critical"
    assert diagnostics["critical_count"] >= 1
    assert any(finding["code"] == "critical_validation_pressure" for finding in diagnostics["findings"])
    assert any(finding["code"] == "invalid_adapter_packet" for finding in diagnostics["findings"])


def test_warning_diagnostics():
    report = clean_health_report()
    record = report["records"][0]
    record["warning_count"] = 2
    record["issue_count"] = 2
    record["health_score"] = 82.0
    record["health_status"] = "adapter_watch"
    record["institutional_ready"] = False

    diagnostics = oracle_universal_market_adapter_diagnostics_engine.diagnose(report)

    assert diagnostics["diagnostics_status"] == "adapter_diagnostics_warnings"
    assert diagnostics["warning_count"] >= 1
    assert any(finding["code"] == "warning_validation_pressure" for finding in diagnostics["findings"])


def test_safety_failure_diagnostics():
    report = clean_health_report()
    record = report["records"][0]
    record["execution_allowed"] = True
    record["safety_status"] = "safety_failed_execution_allowed"

    diagnostics = oracle_universal_market_adapter_diagnostics_engine.diagnose(report)

    assert diagnostics["diagnostics_status"] == "adapter_diagnostics_critical"
    assert any(finding["code"] == "execution_contract_failure" for finding in diagnostics["findings"])
    assert any(finding["code"] == "safety_status_failure" for finding in diagnostics["findings"])


def test_lookup_adapter_findings():
    diagnostics = oracle_universal_market_adapter_diagnostics_engine.diagnose(clean_health_report())
    lookup = oracle_universal_market_adapter_diagnostics_engine.lookup_adapter_findings(diagnostics, "adp.crypto")

    assert lookup["found"] is True
    assert lookup["finding_count"] == 1
    assert lookup["findings"][0]["adapter_id"] == "adp.crypto"
    assert lookup["read_only"] is True


if __name__ == "__main__":
    test_clean_diagnostics()
    test_critical_diagnostics()
    test_warning_diagnostics()
    test_safety_failure_diagnostics()
    test_lookup_adapter_findings()
    print("[PASS] OI-170 Oracle Universal Market Adapter Diagnostics Engine")
