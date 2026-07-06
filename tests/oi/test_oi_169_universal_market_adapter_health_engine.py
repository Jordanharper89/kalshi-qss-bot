from qseries_v2.oracle_intelligence.universal_market_adapter_health_engine import (
    oracle_universal_market_adapter_health_engine,
)


def telemetry():
    return {
        "adapter_telemetry_id": "tel-001",
        "telemetry_status": "adapter_telemetry_institutional",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "records": [
            {
                "telemetry_record_id": "tel-rec-001",
                "adapter_id": "adp.crypto",
                "domain": "CRYPTO",
                "validation_status": "adapter_packet_valid",
                "record_count": 3,
                "issue_count": 0,
                "critical_count": 0,
                "warning_count": 0,
                "health_score": 100.0,
                "health_status": "institutional_adapter_health",
                "lineage_hash": "abc123",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            }
        ],
    }


def test_health_report_institutional():
    report = oracle_universal_market_adapter_health_engine.evaluate(telemetry())

    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["health_report_status"] == "adapter_health_institutional"
    assert report["adapter_count"] == 1
    assert report["domain_count"] == 1
    assert report["institutional_ready_count"] == 1
    assert report["average_health_score"] == 100.0


def test_warning_health_report():
    data = telemetry()
    data["records"][0]["warning_count"] = 2
    data["records"][0]["issue_count"] = 2
    data["records"][0]["health_score"] = 88.0

    report = oracle_universal_market_adapter_health_engine.evaluate(data)

    assert report["health_report_status"] == "adapter_health_ready_with_warnings"
    assert report["total_warning_count"] == 2
    assert report["total_critical_count"] == 0


def test_critical_health_report():
    data = telemetry()
    data["records"][0]["critical_count"] = 1
    data["records"][0]["issue_count"] = 1
    data["records"][0]["health_score"] = 55.0
    data["records"][0]["validation_status"] = "adapter_packet_invalid"

    report = oracle_universal_market_adapter_health_engine.evaluate(data)

    assert report["health_report_status"] == "adapter_health_critical"
    assert report["total_critical_count"] == 1
    assert report["records"][0]["health_status"] == "adapter_health_critical"


def test_lookup_adapter():
    report = oracle_universal_market_adapter_health_engine.evaluate(telemetry())
    lookup = oracle_universal_market_adapter_health_engine.lookup_adapter(report, "adp.crypto")

    assert lookup["found"] is True
    assert lookup["adapter_id"] == "adp.crypto"
    assert lookup["average_health_score"] == 100.0
    assert lookup["read_only"] is True
    assert lookup["execution_allowed"] is False


def test_empty_health_report():
    report = oracle_universal_market_adapter_health_engine.evaluate({
        "adapter_telemetry_id": "empty",
        "records": [],
    })

    assert report["health_report_status"] == "empty_adapter_health_report"
    assert report["health_record_count"] == 0
    assert report["records"] == []
    assert report["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_health_report_institutional()
    test_warning_health_report()
    test_critical_health_report()
    test_lookup_adapter()
    test_empty_health_report()
    print("[PASS] OI-169 Oracle Universal Market Adapter Health Engine")
