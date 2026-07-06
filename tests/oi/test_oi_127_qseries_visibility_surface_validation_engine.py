
from qseries_v2.oracle_intelligence.qseries_visibility_surface_validation_engine import qseries_visibility_surface_validation_engine


def test_oi_127_qseries_visibility_surface_validation_engine():
    surface = {
        "status": "ok",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "surface_status": "visible",
        "q_series_visibility_ready": True,
        "oracle_surface_boundaries": [
            "Oracle visibility surface is read-only.",
            "Oracle does not execute.",
            "Q Series owns execution evaluation and decisions.",
        ],
        "surface_cards": [
            {
                "market": "CRYPTO",
                "surface_rank": 1,
                "surface_score": 100.0,
                "surface_tier": "critical",
                "dashboard_tier": "critical",
                "receipt_tier": "critical",
                "transfer_tier": "critical",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
                "surface_note": "CRYPTO Q Series visibility tier is critical.",
            },
            {
                "market": "NASDAQ",
                "surface_rank": 2,
                "surface_score": 100.0,
                "surface_tier": "critical",
                "dashboard_tier": "critical",
                "receipt_tier": "critical",
                "transfer_tier": "critical",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
                "surface_note": "NASDAQ Q Series visibility tier is critical.",
            },
        ],
    }

    report = qseries_visibility_surface_validation_engine.validate_surface(surface)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["validation_status"] == "validated"
    assert report["surface_ready_for_qseries"] is True
    assert report["failed_checks"] == 0
    assert report["validation_score"] == 100.0

    diag = qseries_visibility_surface_validation_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["surface_ready_for_qseries"] is True

    print("[PASS] OI-127 Q Series Visibility Surface Validation Engine")
    print({
        "validation_score": report["validation_score"],
        "validation_status": report["validation_status"],
        "surface_ready": report["surface_ready_for_qseries"],
        "summary": report["validation_summary"],
    })


if __name__ == "__main__":
    test_oi_127_qseries_visibility_surface_validation_engine()
