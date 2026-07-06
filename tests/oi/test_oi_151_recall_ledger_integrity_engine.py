from qseries_v2.oracle_intelligence.recall_ledger_integrity_engine import (
    compute_integrity_hash,
    oracle_recall_ledger_integrity_engine,
)


def test_valid_record_passes():
    record = {
        "ledger_id": "ledger-001",
        "recall_id": "recall-001",
        "receipt_id": "receipt-001",
        "created_at": "2026-07-02T00:00:00+00:00",
        "record_type": "recall_ledger_entry",
        "payload_hash": "abc123",
    }
    record["integrity_hash"] = compute_integrity_hash(record)

    report = oracle_recall_ledger_integrity_engine.validate_record(record)

    assert report["read_only"] is True
    assert report["status"] == "valid"
    assert report["issue_count"] == 0


def test_missing_required_field_fails():
    record = {
        "ledger_id": "ledger-002",
        "recall_id": "recall-002",
        "created_at": "2026-07-02T00:00:00+00:00",
        "record_type": "recall_ledger_entry",
        "payload_hash": "abc123",
    }

    report = oracle_recall_ledger_integrity_engine.validate_record(record)

    assert report["status"] == "invalid"
    assert report["issue_count"] >= 1
    assert any(i["code"] == "missing_required_field" for i in report["issues"])


def test_hash_mismatch_fails():
    record = {
        "ledger_id": "ledger-003",
        "recall_id": "recall-003",
        "receipt_id": "receipt-003",
        "created_at": "2026-07-02T00:00:00+00:00",
        "record_type": "recall_ledger_entry",
        "payload_hash": "abc123",
        "integrity_hash": "bad-hash",
    }

    report = oracle_recall_ledger_integrity_engine.validate_record(record)

    assert report["status"] == "invalid"
    assert any(i["code"] == "hash_mismatch" for i in report["issues"])


def test_batch_validation():
    valid = {
        "ledger_id": "ledger-004",
        "recall_id": "recall-004",
        "receipt_id": "receipt-004",
        "created_at": "2026-07-02T00:00:00+00:00",
        "record_type": "recall_ledger_entry",
        "payload_hash": "abc123",
    }
    valid["integrity_hash"] = compute_integrity_hash(valid)

    invalid = {"ledger_id": "ledger-005"}

    batch = oracle_recall_ledger_integrity_engine.validate_batch([valid, invalid])

    assert batch["read_only"] is True
    assert batch["records_checked"] == 2
    assert batch["invalid_records"] == 1
    assert batch["batch_status"] == "invalid"


if __name__ == "__main__":
    test_valid_record_passes()
    test_missing_required_field_fails()
    test_hash_mismatch_fails()
    test_batch_validation()
    print("[PASS] OI-151 Oracle Recall Ledger Integrity Engine")
