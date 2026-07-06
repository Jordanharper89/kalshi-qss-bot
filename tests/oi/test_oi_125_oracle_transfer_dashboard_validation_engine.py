
from qseries_v2.oracle_intelligence.oracle_transfer_dashboard_validation_engine import oracle_transfer_dashboard_validation_engine


def test_oi_125_oracle_transfer_dashboard_validation_engine():
    dashboard = {
        "status": "ok",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "dashboard_status": "confirmed_visible",
        "receipt_confirmed": True,
        "ledger_integrity_confirmed": True,
        "transfer_ready": True,
        "card_count": 2,
        "oracle_dashboard_boundaries": [
            "Oracle transfer dashboard is read-only.",
            "Oracle does not execute.",
            "Q Series owns execution evaluation and decisions.",
        ],
        "dashboard_cards": [
            {
                "market": "CRYPTO",
                "dashboard_rank": 1,
                "dashboard_score": 100.0,
                "dashboard_tier": "critical",
                "receipt_tier": "critical",
                "transfer_tier": "critical",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
                "dashboard_note": "CRYPTO dashboard tier is critical.",
            },
            {
                "market": "NASDAQ",
                "dashboard_rank": 2,
                "dashboard_score": 100.0,
                "dashboard_tier": "critical",
                "receipt_tier": "critical",
                "transfer_tier": "critical",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
                "dashboard_note": "NASDAQ dashboard tier is critical.",
            },
        ],
    }

    report = oracle_transfer_dashboard_validation_engine.validate_dashboard(dashboard)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["validation_status"] == "validated"
    assert report["dashboard_ready"] is True
    assert report["failed_checks"] == 0
    assert report["validation_score"] == 100.0

    diag = oracle_transfer_dashboard_validation_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["dashboard_ready"] is True

    print("[PASS] OI-125 Oracle Transfer Dashboard Validation Engine")
    print({
        "validation_score": report["validation_score"],
        "validation_status": report["validation_status"],
        "dashboard_ready": report["dashboard_ready"],
        "summary": report["validation_summary"],
    })


if __name__ == "__main__":
    test_oi_125_oracle_transfer_dashboard_validation_engine()
