
from qseries_v2.oracle_intelligence.oracle_handoff_manifest_engine import oracle_handoff_manifest_engine


def test_oi_117_oracle_handoff_manifest_engine():
    handoff = {
        "handoff_score": 86.2,
        "handoff_posture": "urgent_handoff",
        "handoff_items": [
            {
                "market": "CRYPTO",
                "handoff_rank": 1,
                "handoff_score": 90.2,
                "handoff_tier": "critical",
                "digest_tier": "critical",
                "support_tier": "critical",
                "review_conclusion": "high_confidence_review",
                "oracle_observation": "Keep market in elevated Oracle observation rotation.",
                "execution_allowed": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
            {
                "market": "NASDAQ",
                "handoff_rank": 2,
                "handoff_score": 72.0,
                "handoff_tier": "high",
                "digest_tier": "elevated",
                "support_tier": "high",
                "review_conclusion": "confirmed_review",
                "oracle_observation": "Oracle review packet is ready for read-only downstream visibility.",
                "execution_allowed": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
        ],
    }

    validation = {
        "validation_status": "validated",
        "validation_score": 100.0,
        "failed_checks": 0,
        "handoff_ready_for_q_series_visibility": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
    }

    manifest = oracle_handoff_manifest_engine.build_manifest(handoff, validation)

    assert manifest["status"] == "ok"
    assert manifest["read_only"] is True
    assert manifest["execution_allowed"] is False
    assert manifest["execution_owner"] == "Q Series"
    assert manifest["manifest_status"] == "ready"
    assert manifest["q_series_visibility_ready"] is True
    assert manifest["handoff_count"] == 2
    assert manifest["manifest_items"][0]["market"] == "CRYPTO"
    assert manifest["manifest_summary"]["execution_allowed"] is False

    diag = oracle_handoff_manifest_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["q_series_visibility_ready"] is True

    print("[PASS] OI-117 Oracle Handoff Manifest Engine")
    print({
        "manifest_status": manifest["manifest_status"],
        "ready": manifest["q_series_visibility_ready"],
        "summary": manifest["manifest_summary"],
        "top": manifest["manifest_items"][0],
    })


if __name__ == "__main__":
    test_oi_117_oracle_handoff_manifest_engine()
