from qseries_v2.oracle_intelligence.universal_market_adapter_lifecycle_engine import (
    oracle_universal_market_adapter_lifecycle_engine,
)


def institutional_certification():
    return {
        "adapter_certification_batch_id": "cert-batch-001",
        "certification_status": "adapter_certification_institutional",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "records": [
            {
                "certification_id": "cert-001",
                "adapter_id": "adp.crypto",
                "domain": "CRYPTO",
                "certification_score": 100.0,
                "certification_tier": "institutional_certification",
                "certification_status": "adapter_institutionally_certified",
                "critical_count": 0,
                "warning_count": 0,
                "certified": True,
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            }
        ],
    }


def test_institutional_lifecycle():
    report = oracle_universal_market_adapter_lifecycle_engine.evaluate(institutional_certification())

    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["lifecycle_status"] == "adapter_lifecycle_institutional"
    assert report["adapter_count"] == 1
    assert report["promoted_count"] == 1
    assert report["blocked_count"] == 0
    assert report["records"][0]["lifecycle_state"] == "active_institutional_read_only"


def test_active_review_lifecycle():
    cert = institutional_certification()
    cert["records"][0]["certification_score"] = 80.0
    cert["records"][0]["certification_status"] = "adapter_certified_with_review"
    cert["records"][0]["warning_count"] = 2

    report = oracle_universal_market_adapter_lifecycle_engine.evaluate(cert)

    assert report["lifecycle_status"] == "adapter_lifecycle_active"
    assert report["records"][0]["lifecycle_state"] == "active_review_read_only"
    assert report["promoted_count"] == 1


def test_blocked_lifecycle():
    cert = institutional_certification()
    cert["records"][0]["certification_status"] = "adapter_certification_blocked"
    cert["records"][0]["critical_count"] = 1
    cert["records"][0]["certified"] = False

    report = oracle_universal_market_adapter_lifecycle_engine.evaluate(cert)

    assert report["lifecycle_status"] == "adapter_lifecycle_blocked"
    assert report["blocked_count"] == 1
    assert report["records"][0]["lifecycle_state"] == "blocked"


def test_lookup_adapter():
    report = oracle_universal_market_adapter_lifecycle_engine.evaluate(institutional_certification())
    result = oracle_universal_market_adapter_lifecycle_engine.lookup_adapter(report, "adp.crypto")

    assert result["found"] is True
    assert result["record"]["adapter_id"] == "adp.crypto"
    assert result["read_only"] is True
    assert result["execution_allowed"] is False


def test_empty_lifecycle():
    report = oracle_universal_market_adapter_lifecycle_engine.evaluate({
        "adapter_certification_batch_id": "empty",
        "records": [],
    })

    assert report["lifecycle_status"] == "empty_adapter_lifecycle"
    assert report["adapter_count"] == 0
    assert report["records"] == []
    assert report["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_institutional_lifecycle()
    test_active_review_lifecycle()
    test_blocked_lifecycle()
    test_lookup_adapter()
    test_empty_lifecycle()
    print("[PASS] OI-172 Oracle Universal Market Adapter Lifecycle Engine")
