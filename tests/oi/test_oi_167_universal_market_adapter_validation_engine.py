from qseries_v2.oracle_intelligence.universal_market_adapter_validation_engine import (
    oracle_universal_market_adapter_validation_engine,
)


def valid_packet():
    return {
        "adapter_id": "adp.crypto",
        "domain": "CRYPTO",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "records": [
            {
                "umm_record_id": "umm-001",
                "domain": "CRYPTO",
                "symbol": "SOL-USD",
                "timestamp": "2026-07-02T00:00:00+00:00",
                "source": "crypto_adapter",
                "price": 144.25,
                "confidence": 91.0,
                "lineage": "lineage-001",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
                "telemetry": {"latency_ms": 12},
            }
        ],
    }


def test_valid_packet_passes():
    report = oracle_universal_market_adapter_validation_engine.validate_packet(valid_packet())

    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["validation_status"] == "adapter_packet_valid"
    assert report["issue_count"] == 0
    assert report["record_count"] == 1


def test_packet_execution_violation_fails():
    packet = valid_packet()
    packet["execution_allowed"] = True

    report = oracle_universal_market_adapter_validation_engine.validate_packet(packet)

    assert report["validation_status"] == "adapter_packet_invalid"
    assert report["critical_count"] >= 1
    assert any(issue["code"] == "packet_execution_violation" for issue in report["issues"])


def test_record_execution_violation_fails():
    packet = valid_packet()
    packet["records"][0]["execution_allowed"] = True

    report = oracle_universal_market_adapter_validation_engine.validate_packet(packet)

    assert report["validation_status"] == "adapter_packet_invalid"
    assert any(issue["code"] == "record_execution_violation" for issue in report["issues"])


def test_domain_mismatch_fails():
    packet = valid_packet()
    packet["records"][0]["domain"] = "STOCKS"

    report = oracle_universal_market_adapter_validation_engine.validate_packet(packet)

    assert report["validation_status"] == "adapter_packet_invalid"
    assert any(issue["code"] == "domain_mismatch" for issue in report["issues"])


def test_unsupported_domain_warns():
    packet = valid_packet()
    packet["domain"] = "UNKNOWN_DOMAIN"
    packet["records"][0]["domain"] = "UNKNOWN_DOMAIN"

    report = oracle_universal_market_adapter_validation_engine.validate_packet(packet)

    assert report["validation_status"] == "adapter_packet_valid_with_warnings"
    assert report["warning_count"] == 1
    assert any(issue["code"] == "unsupported_packet_domain" for issue in report["issues"])


def test_batch_validation():
    batch = oracle_universal_market_adapter_validation_engine.validate_batch([
        valid_packet(),
        valid_packet(),
    ])

    assert batch["batch_status"] == "adapter_validation_batch_valid"
    assert batch["packet_count"] == 2
    assert batch["valid_count"] == 2
    assert batch["invalid_count"] == 0


if __name__ == "__main__":
    test_valid_packet_passes()
    test_packet_execution_violation_fails()
    test_record_execution_violation_fails()
    test_domain_mismatch_fails()
    test_unsupported_domain_warns()
    test_batch_validation()
    print("[PASS] OI-167 Oracle Universal Market Adapter Validation Engine")
