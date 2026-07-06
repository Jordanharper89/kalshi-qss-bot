
from qseries_v2.oracle_intelligence.qseries_visibility_release_engine import qseries_visibility_release_engine


def test_oi_128_qseries_visibility_release_engine():
    surface = {
        "status": "ok",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "surface_status": "visible",
        "q_series_visibility_ready": True,
        "surface_cards": [
            {
                "market": "CRYPTO",
                "surface_rank": 1,
                "surface_score": 100.0,
                "surface_tier": "critical",
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
                "surface_rank": 2,
                "surface_score": 100.0,
                "surface_tier": "critical",
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
        "surface_ready_for_qseries": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
    }

    release = qseries_visibility_release_engine.build_release(surface, validation)

    assert release["status"] == "ok"
    assert release["read_only"] is True
    assert release["execution_allowed"] is False
    assert release["execution_owner"] == "Q Series"
    assert release["release_status"] == "released"
    assert release["release_confirmed"] is True
    assert release["release_count"] == 2
    assert release["release_items"][0]["release_rank"] == 1
    assert release["release_items"][0]["market"] == "CRYPTO"
    assert release["release_summary"]["execution_allowed"] is False

    diag = qseries_visibility_release_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["release_confirmed"] is True

    print("[PASS] OI-128 Q Series Visibility Release Engine")
    print({
        "release_status": release["release_status"],
        "release_confirmed": release["release_confirmed"],
        "summary": release["release_summary"],
        "top": release["release_items"][0],
    })


if __name__ == "__main__":
    test_oi_128_qseries_visibility_release_engine()
