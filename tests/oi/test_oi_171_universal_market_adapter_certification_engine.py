from qseries_v2.oracle_intelligence.universal_market_adapter_certification_engine import (
    oracle_universal_market_adapter_certification_engine,
)


def clean_diagnostics():
    return {
        "adapter_diagnostics_id": "diag-001",
        "diagnostics_status": "adapter_diagnostics_clean",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "findings": [
            {
                "finding_id": "find-001",
                "adapter_id": "adp.crypto",
                "domain": "CRYPTO",
                "severity": "info",
                "code": "adapter_diagnostics_clean",
                "message": "Adapter diagnostics are clean.",
                "recommendation": "Adapter may remain active.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            }
        ],
    }


def test_clean_certification():
    cert = oracle_universal_market_adapter_certification_engine.certify(clean_diagnostics())

    assert cert["read_only"] is True
    assert cert["execution_allowed"] is False
    assert cert["execution_owner"] == "Q Series"
    assert cert["certification_status"] == "adapter_certification_institutional"
    assert cert["adapter_count"] == 1
    assert cert["certified_count"] == 1
    assert cert["blocked_count"] == 0
    assert cert["records"][0]["certified"] is True


def test_warning_certification_ready():
    diag = clean_diagnostics()
    diag["findings"].append({
        "finding_id": "find-002",
        "adapter_id": "adp.crypto",
        "domain": "CRYPTO",
        "severity": "warning",
        "code": "warning_validation_pressure",
        "message": "Warning pressure.",
        "recommendation": "Review warnings.",
    })

    cert = oracle_universal_market_adapter_certification_engine.certify(diag)

    assert cert["certification_status"] == "adapter_certification_ready"
    assert cert["warning_count"] == 1
    assert cert["records"][0]["certified"] is True


def test_critical_certification_blocked():
    diag = clean_diagnostics()
    diag["findings"].append({
        "finding_id": "find-003",
        "adapter_id": "adp.crypto",
        "domain": "CRYPTO",
        "severity": "critical",
        "code": "execution_contract_failure",
        "message": "Execution contract failed.",
        "recommendation": "Block adapter.",
    })

    cert = oracle_universal_market_adapter_certification_engine.certify(diag)

    assert cert["certification_status"] == "adapter_certification_blocked"
    assert cert["blocked_count"] == 1
    assert cert["critical_count"] == 1
    assert cert["records"][0]["certified"] is False


def test_lookup_certification():
    cert = oracle_universal_market_adapter_certification_engine.certify(clean_diagnostics())
    result = oracle_universal_market_adapter_certification_engine.lookup_certification(cert, "adp.crypto")

    assert result["found"] is True
    assert result["record"]["adapter_id"] == "adp.crypto"
    assert result["read_only"] is True
    assert result["execution_allowed"] is False


def test_empty_certification():
    cert = oracle_universal_market_adapter_certification_engine.certify({
        "adapter_diagnostics_id": "empty",
        "diagnostics_status": "empty_adapter_diagnostics",
        "findings": [],
    })

    assert cert["certification_status"] == "empty_adapter_certification"
    assert cert["adapter_count"] == 0
    assert cert["records"] == []
    assert cert["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_clean_certification()
    test_warning_certification_ready()
    test_critical_certification_blocked()
    test_lookup_certification()
    test_empty_certification()
    print("[PASS] OI-171 Oracle Universal Market Adapter Certification Engine")
