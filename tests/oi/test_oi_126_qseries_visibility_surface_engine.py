
from qseries_v2.oracle_intelligence.qseries_visibility_surface_engine import qseries_visibility_surface_engine


def test_oi_126_qseries_visibility_surface_engine():
    dashboard = {
        "status": "ok",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "dashboard_status": "confirmed_visible",
        "receipt_confirmed": True,
        "ledger_integrity_confirmed": True,
        "transfer_ready": True,
        "dashboard_cards": [
            {
                "market": "CRYPTO",
                "dashboard_rank": 1,
                "dashboard_score": 100.0,
                "dashboard_tier": "critical",
                "receipt_tier": "critical",
                "transfer_tier": "critical",
                "review_conclusion": "high_confidence_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
            {
                "market": "NASDAQ",
                "dashboard_rank": 2,
                "dashboard_score": 92.0,
                "dashboard_tier": "critical",
                "receipt_tier": "critical",
                "transfer_tier": "critical",
                "review_conclusion": "confirmed_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
        ],
    }

    validation = {
        "validation_status": "validated",
        "validation_score": 100.0,
        "dashboard_ready": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
    }

    surface = qseries_visibility_surface_engine.build_visibility_surface(dashboard, validation)

    assert surface["status"] == "ok"
    assert surface["read_only"] is True
    assert surface["execution_allowed"] is False
    assert surface["execution_owner"] == "Q Series"
    assert surface["surface_status"] == "visible"
    assert surface["q_series_visibility_ready"] is True
    assert surface["surface_count"] == 2
    assert surface["surface_cards"][0]["surface_rank"] == 1
    assert surface["surface_cards"][0]["market"] == "CRYPTO"
    assert surface["surface_summary"]["execution_allowed"] is False

    diag = qseries_visibility_surface_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["surface_status"] == "visible"

    print("[PASS] OI-126 Q Series Visibility Surface Engine")
    print({
        "surface_status": surface["surface_status"],
        "surface_count": surface["surface_count"],
        "summary": surface["surface_summary"],
        "top": surface["surface_cards"][0],
    })


if __name__ == "__main__":
    test_oi_126_qseries_visibility_surface_engine()
