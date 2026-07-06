from qseries_v2.oracle_intelligence.universal_market_adapter_telemetry_engine import (
    oracle_universal_market_adapter_telemetry_engine,
)


def valid_report():
    return {
        "adapter_validation_id": "val-001",
        "validation_status": "adapter_packet_valid",
        "adapter_id": "adp.crypto",
        "domain": "CRYPTO",
        "record_count": 3,
        "issue_count": 0,
        "critical_count": 0,
        "warning_count": 0,
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
    }


def warning_report():
    report = valid_report()
    report["adapter_validation_id"] = "val-002"
    report["adapter_id"] = "adp.stocks"
    report["domain"] = "STOCKS"
    report["validation_status"] = "adapter_packet_valid_with_warnings"
    report["issue_count"] = 2
    report["warning_count"] = 2
    return report


def invalid_report():
    report = valid_report()
    report["adapter_validation_id"] = "val-003"
    report["adapter_id"] = "adp.forex"
    report["domain"] = "FOREX"
    report["validation_status"] = "adapter_packet_invalid"
    report["issue_count"] = 1
    report["critical_count"] = 1
    return report


def test_collect_valid_telemetry():
    telemetry = oracle_universal_market_adapter_telemetry_engine.collect([valid_report()])

    assert telemetry["read_only"] is True
    assert telemetry["execution_allowed"] is False
    assert telemetry["execution_owner"] == "Q Series"
    assert telemetry["telemetry_status"] == "adapter_telemetry_institutional"
    assert telemetry["adapter_count"] == 1
    assert telemetry["domain_count"] == 1
    assert telemetry["average_health_score"] == 100.0


def test_collect_warning_telemetry():
    telemetry = oracle_universal_market_adapter_telemetry_engine.collect([valid_report(), warning_report()])

    assert telemetry["telemetry_status"] == "adapter_telemetry_warnings"
    assert telemetry["total_warning_count"] == 2
    assert telemetry["total_critical_count"] == 0
    assert telemetry["adapter_count"] == 2


def test_collect_critical_telemetry():
    telemetry = oracle_universal_market_adapter_telemetry_engine.collect([valid_report(), invalid_report()])

    assert telemetry["telemetry_status"] == "adapter_telemetry_critical"
    assert telemetry["total_critical_count"] == 1
    assert telemetry["total_issue_count"] == 1


def test_adapter_health_lookup():
    telemetry = oracle_universal_market_adapter_telemetry_engine.collect([valid_report(), warning_report()])
    health = oracle_universal_market_adapter_telemetry_engine.adapter_health(telemetry, "adp.crypto")

    assert health["found"] is True
    assert health["adapter_id"] == "adp.crypto"
    assert health["average_health_score"] == 100.0
    assert health["read_only"] is True
    assert health["execution_allowed"] is False


def test_empty_telemetry():
    telemetry = oracle_universal_market_adapter_telemetry_engine.collect([])

    assert telemetry["telemetry_status"] == "empty_adapter_telemetry"
    assert telemetry["telemetry_record_count"] == 0
    assert telemetry["records"] == []
    assert telemetry["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_collect_valid_telemetry()
    test_collect_warning_telemetry()
    test_collect_critical_telemetry()
    test_adapter_health_lookup()
    test_empty_telemetry()
    print("[PASS] OI-168 Oracle Universal Market Adapter Telemetry Engine")
