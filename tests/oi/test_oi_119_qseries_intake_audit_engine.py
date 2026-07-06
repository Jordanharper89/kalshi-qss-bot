
from qseries_v2.oracle_intelligence.qseries_intake_audit_engine import qseries_intake_audit_engine


def test_oi_119_qseries_intake_audit_engine():
    intake_packet = {
        "status": "ok",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "q_series_visibility_ready": True,
        "intake_status": "ready",
        "oracle_boundary_notice": [
            "This is an Oracle read-only intake packet.",
            "Oracle does not execute.",
            "Q Series is the execution owner.",
        ],
        "intake_items": [
            {
                "market": "CRYPTO",
                "intake_score": 100.0,
                "intake_tier": "critical",
                "intake_rank": 1,
                "handoff_rank": 1,
                "handoff_score": 90.2,
                "handoff_tier": "critical",
                "review_conclusion": "high_confidence_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
                "intake_note": "CRYPTO intake tier is critical.",
            },
            {
                "market": "NASDAQ",
                "intake_score": 81.0,
                "intake_tier": "high",
                "intake_rank": 2,
                "handoff_rank": 2,
                "handoff_score": 72.0,
                "handoff_tier": "high",
                "review_conclusion": "confirmed_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
                "intake_note": "NASDAQ intake tier is high.",
            },
        ],
    }

    audit = qseries_intake_audit_engine.audit_intake_packet(intake_packet)

    assert audit["status"] == "ok"
    assert audit["read_only"] is True
    assert audit["execution_allowed"] is False
    assert audit["execution_owner"] == "Q Series"
    assert audit["audit_status"] == "passed"
    assert audit["failed_checks"] == 0
    assert audit["q_series_safe_to_view"] is True
    assert audit["audit_score"] == 100.0

    diag = qseries_intake_audit_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["q_series_safe_to_view"] is True

    print("[PASS] OI-119 Q Series Intake Audit Engine")
    print({
        "audit_score": audit["audit_score"],
        "audit_status": audit["audit_status"],
        "safe_to_view": audit["q_series_safe_to_view"],
        "summary": audit["audit_summary"],
    })


if __name__ == "__main__":
    test_oi_119_qseries_intake_audit_engine()
