from qseries_v2.oracle_intelligence.universal_market_model_schema_engine import (
    oracle_universal_market_model_schema_engine,
)


def test_schema_contract_is_read_only():
    schema = oracle_universal_market_model_schema_engine.schema()

    assert schema["read_only"] is True
    assert schema["execution_allowed"] is False
    assert schema["execution_owner"] == "Q Series"
    assert "domain" in schema["required_fields"]
    assert "CRYPTO" in schema["supported_domains"]


def test_normalize_record():
    record = oracle_universal_market_model_schema_engine.normalize_record({
        "domain": "crypto",
        "ticker": "SOL-USD",
        "source": "crypto_adapter",
        "value": 144.25,
        "confidence": 88,
        "lineage_hash": "abc123",
    })

    assert record["domain"] == "CRYPTO"
    assert record["symbol"] == "SOL-USD"
    assert record["price"] == 144.25
    assert record["confidence"] == 88.0
    assert record["read_only"] is True
    assert record["execution_allowed"] is False


def test_valid_record_passes():
    report = oracle_universal_market_model_schema_engine.validate_record({
        "domain": "STOCKS",
        "symbol": "AAPL",
        "timestamp": "2026-07-02T00:00:00+00:00",
        "source": "stocks_adapter",
        "price": 200.0,
        "confidence": 91.0,
        "lineage": "lineage-001",
    })

    assert report["validation_status"] == "umm_record_valid"
    assert report["issue_count"] == 0
    assert report["normalized_record"]["execution_owner"] == "Q Series"


def test_unsupported_domain_warns():
    report = oracle_universal_market_model_schema_engine.validate_record({
        "domain": "UNKNOWN_DOMAIN",
        "symbol": "X",
        "timestamp": "2026-07-02T00:00:00+00:00",
        "source": "adapter",
        "price": 1,
        "confidence": 70,
        "lineage": "lineage-002",
    })

    assert report["validation_status"] == "umm_record_valid_with_warnings"
    assert report["warning_count"] == 1
    assert any(issue["code"] == "unsupported_domain" for issue in report["issues"])


def test_batch_validation():
    batch = oracle_universal_market_model_schema_engine.validate_batch([
        {
            "domain": "CRYPTO",
            "symbol": "BTC-USD",
            "source": "crypto_adapter",
            "price": 100,
            "confidence": 90,
            "lineage": "a",
        },
        {
            "domain": "FOREX",
            "symbol": "EURUSD",
            "source": "forex_adapter",
            "price": 1.1,
            "confidence": 84,
            "lineage": "b",
        },
    ])

    assert batch["batch_status"] == "umm_batch_valid"
    assert batch["record_count"] == 2
    assert batch["valid_count"] == 2
    assert batch["invalid_count"] == 0


if __name__ == "__main__":
    test_schema_contract_is_read_only()
    test_normalize_record()
    test_valid_record_passes()
    test_unsupported_domain_warns()
    test_batch_validation()
    print("[PASS] OI-165 Oracle Universal Market Model Schema Engine")
