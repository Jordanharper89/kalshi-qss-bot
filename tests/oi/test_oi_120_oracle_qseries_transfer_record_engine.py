
from qseries_v2.oracle_intelligence.oracle_qseries_transfer_record_engine import oracle_qseries_transfer_record_engine


def test_oi_120_oracle_qseries_transfer_record_engine():
    intake_packet = {
        "status": "ok",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "q_series_visibility_ready": True,
        "intake_status": "ready",
        "intake_items": [
            {
                "market": "CRYPTO",
                "intake_score": 100.0,
                "intake_tier": "critical",
                "intake_rank": 1,
                "handoff_score": 90.2,
                "handoff_tier": "critical",
                "review_conclusion": "high_confidence_review",
                "oracle_observation": "Keep market in elevated Oracle observation rotation.",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
            {
                "market": "NASDAQ",
                "intake_score": 81.0,
                "intake_tier": "high",
                "intake_rank": 2,
                "handoff_score": 72.0,
                "handoff_tier": "high",
                "review_conclusion": "confirmed_review",
                "oracle_observation": "Oracle review packet is ready for read-only downstream visibility.",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
        ],
    }

    intake_audit = {
        "audit_status": "passed",
        "audit_score": 100.0,
        "q_series_safe_to_view": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
    }

    record = oracle_qseries_transfer_record_engine.build_transfer_record(intake_packet, intake_audit)

    assert record["status"] == "ok"
    assert record["read_only"] is True
    assert record["execution_allowed"] is False
    assert record["execution_owner"] == "Q Series"
    assert record["transfer_ready"] is True
    assert record["transfer_status"] == "ready_for_q_series_visibility"
    assert record["transfer_count"] == 2
    assert record["transfer_items"][0]["transfer_rank"] == 1
    assert record["transfer_items"][0]["market"] == "CRYPTO"
    assert record["transfer_summary"]["execution_allowed"] is False

    diag = oracle_qseries_transfer_record_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["transfer_ready"] is True

    print("[PASS] OI-120 Oracle Q Series Transfer Record Engine")
    print({
        "transfer_status": record["transfer_status"],
        "transfer_ready": record["transfer_ready"],
        "summary": record["transfer_summary"],
        "top": record["transfer_items"][0],
    })


if __name__ == "__main__":
    test_oi_120_oracle_qseries_transfer_record_engine()
