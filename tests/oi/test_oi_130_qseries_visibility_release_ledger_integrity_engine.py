
from qseries_v2.oracle_intelligence.qseries_visibility_release_ledger_integrity_engine import qseries_visibility_release_ledger_integrity_engine
import hashlib
import json


def test_oi_130_qseries_visibility_release_ledger_integrity_engine():
    release_items = [
        {
            "market": "CRYPTO",
            "release_rank": 1,
            "release_score": 100.0,
            "release_tier": "critical",
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
            "release_rank": 2,
            "release_score": 100.0,
            "release_tier": "critical",
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
    ]

    content = {
        "release_status": "released",
        "release_confirmed": True,
        "surface_status": "visible",
        "validation_status": "validated",
        "items": release_items,
    }

    ledger_id = hashlib.sha256(json.dumps(content, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:24]

    release_ledger = {
        "status": "ok",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "release_ledger_id": ledger_id,
        "release_ledger_status": "recorded_released_visibility",
        "release_status": "released",
        "release_confirmed": True,
        "surface_status": "visible",
        "validation_status": "validated",
        "validation_score": 100.0,
        "release_ledger_items": release_items,
        "oracle_release_ledger_boundaries": [
            "Oracle release ledger is read-only.",
            "Oracle does not execute.",
            "Q Series owns execution evaluation and decisions.",
        ],
    }

    report = qseries_visibility_release_ledger_integrity_engine.verify_release_ledger(release_ledger)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["integrity_status"] == "verified"
    assert report["release_ledger_integrity_confirmed"] is True
    assert report["failed_checks"] == 0
    assert report["integrity_score"] == 100.0

    diag = qseries_visibility_release_ledger_integrity_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["release_ledger_integrity_confirmed"] is True

    print("[PASS] OI-130 Q Series Visibility Release Ledger Integrity Engine")
    print({
        "integrity_score": report["integrity_score"],
        "integrity_status": report["integrity_status"],
        "confirmed": report["release_ledger_integrity_confirmed"],
        "summary": report["integrity_summary"],
    })


if __name__ == "__main__":
    test_oi_130_qseries_visibility_release_ledger_integrity_engine()
