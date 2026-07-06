
from qseries_v2.oracle_intelligence.oracle_ledger_integrity_engine import oracle_ledger_integrity_engine
import hashlib
import json


def test_oi_122_oracle_ledger_integrity_engine():
    ledger_items = [
        {
            "market": "CRYPTO",
            "transfer_rank": 1,
            "transfer_score": 100.0,
            "transfer_tier": "critical",
            "intake_tier": "critical",
            "handoff_tier": "critical",
            "review_conclusion": "high_confidence_review",
            "q_series_visibility": True,
            "execution_permission_from_oracle": False,
            "execution_owner": "Q Series",
            "read_only": True,
        },
        {
            "market": "NASDAQ",
            "transfer_rank": 2,
            "transfer_score": 90.0,
            "transfer_tier": "critical",
            "intake_tier": "high",
            "handoff_tier": "high",
            "review_conclusion": "confirmed_review",
            "q_series_visibility": True,
            "execution_permission_from_oracle": False,
            "execution_owner": "Q Series",
            "read_only": True,
        },
    ]

    content = {
        "transfer_status": "ready_for_q_series_visibility",
        "transfer_ready": True,
        "audit_status": "passed",
        "intake_status": "ready",
        "items": ledger_items,
    }

    ledger_id = hashlib.sha256(json.dumps(content, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:24]

    ledger = {
        "status": "ok",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "ledger_entry_id": ledger_id,
        "ledger_status": "recorded_ready_transfer",
        "transfer_status": "ready_for_q_series_visibility",
        "transfer_ready": True,
        "audit_status": "passed",
        "intake_status": "ready",
        "q_series_safe_to_view": True,
        "ledger_items": ledger_items,
        "oracle_boundaries": [
            "Oracle Intelligence is read-only.",
            "Oracle ledger does not execute.",
            "Q Series owns execution evaluation and execution decisions.",
        ],
    }

    report = oracle_ledger_integrity_engine.verify_ledger(ledger)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["integrity_status"] == "verified"
    assert report["ledger_integrity_confirmed"] is True
    assert report["failed_checks"] == 0
    assert report["integrity_score"] == 100.0

    diag = oracle_ledger_integrity_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["ledger_integrity_confirmed"] is True

    print("[PASS] OI-122 Oracle Ledger Integrity Engine")
    print({
        "integrity_score": report["integrity_score"],
        "integrity_status": report["integrity_status"],
        "confirmed": report["ledger_integrity_confirmed"],
        "summary": report["integrity_summary"],
    })


if __name__ == "__main__":
    test_oi_122_oracle_ledger_integrity_engine()
