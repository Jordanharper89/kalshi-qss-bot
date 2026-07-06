
from qseries_v2.oracle_intelligence.oracle_handoff_validation_engine import oracle_handoff_validation_engine


def test_oi_116_oracle_handoff_validation_engine():
    handoff = {
        "status": "ok",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "handoff_score": 86.2,
        "handoff_posture": "urgent_handoff",
        "handoff_summary": {
            "headline": "Oracle handoff posture is urgent_handoff; top market is CRYPTO.",
            "execution_allowed": False,
            "execution_owner": "Q Series",
        },
        "oracle_limits": [
            "Oracle is read-only.",
            "Oracle does not place trades.",
            "Q Series owns execution decisions.",
        ],
        "handoff_items": [
            {
                "market": "CRYPTO",
                "handoff_score": 90.2,
                "handoff_tier": "critical",
                "handoff_rank": 1,
                "handoff_note": "CRYPTO handoff tier is critical.",
                "execution_allowed": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
            {
                "market": "NASDAQ",
                "handoff_score": 72.0,
                "handoff_tier": "high",
                "handoff_rank": 2,
                "handoff_note": "NASDAQ handoff tier is high.",
                "execution_allowed": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
        ],
    }

    report = oracle_handoff_validation_engine.validate_handoff(handoff)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["validation_status"] == "validated"
    assert report["failed_checks"] == 0
    assert report["handoff_ready_for_q_series_visibility"] is True
    assert report["validation_score"] == 100.0

    diag = oracle_handoff_validation_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False

    print("[PASS] OI-116 Oracle Handoff Validation Engine")
    print({
        "validation_score": report["validation_score"],
        "validation_status": report["validation_status"],
        "ready": report["handoff_ready_for_q_series_visibility"],
        "summary": report["validation_summary"],
    })


if __name__ == "__main__":
    test_oi_116_oracle_handoff_validation_engine()
