from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
MOD = PKG / "recall_ledger_integrity_engine.py"
TEST = ROOT / "test_oi_151_recall_ledger_integrity_engine.py"
INIT = PKG / "__init__.py"

MODULE = r'''"""
OI-151 — Oracle Recall Ledger Integrity Engine

Read-only institutional integrity checker for Oracle Recall Ledger records.
Oracle never executes trades, manages positions, or submits orders.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Optional


REQUIRED_LEDGER_FIELDS = (
    "ledger_id",
    "recall_id",
    "receipt_id",
    "created_at",
    "record_type",
    "payload_hash",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_text(value: Any) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(f"{k}:{_stable_text(value[k])}" for k in sorted(value)) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_stable_text(v) for v in value) + "]"
    return repr(value)


def compute_integrity_hash(record: Dict[str, Any]) -> str:
    body = {
        k: v
        for k, v in record.items()
        if k not in {"integrity_hash", "integrity_status", "checked_at"}
    }
    return sha256(_stable_text(body).encode("utf-8")).hexdigest()


@dataclass
class LedgerIntegrityIssue:
    ledger_id: str
    severity: str
    code: str
    message: str


@dataclass
class RecallLedgerIntegrityEngine:
    name: str = "oracle_recall_ledger_integrity_engine"
    version: str = "OI-151"
    read_only: bool = True
    issues: List[LedgerIntegrityIssue] = field(default_factory=list)

    def validate_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        self.issues = []
        ledger_id = str(record.get("ledger_id", "unknown"))

        for field_name in REQUIRED_LEDGER_FIELDS:
            if not record.get(field_name):
                self.issues.append(
                    LedgerIntegrityIssue(
                        ledger_id=ledger_id,
                        severity="critical",
                        code="missing_required_field",
                        message=f"Missing required ledger field: {field_name}",
                    )
                )

        expected = record.get("integrity_hash")
        actual = compute_integrity_hash(record)

        if expected and expected != actual:
            self.issues.append(
                LedgerIntegrityIssue(
                    ledger_id=ledger_id,
                    severity="critical",
                    code="hash_mismatch",
                    message="Ledger integrity hash does not match record contents.",
                )
            )

        status = "valid" if not self.issues else "invalid"

        return {
            "module": self.name,
            "version": self.version,
            "read_only": self.read_only,
            "ledger_id": ledger_id,
            "status": status,
            "checked_at": _utc_now(),
            "expected_hash": expected,
            "computed_hash": actual,
            "issue_count": len(self.issues),
            "issues": [issue.__dict__ for issue in self.issues],
        }

    def validate_batch(self, records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        reports = [self.validate_record(record) for record in records]
        invalid = [r for r in reports if r["status"] != "valid"]

        return {
            "module": self.name,
            "version": self.version,
            "read_only": self.read_only,
            "batch_status": "valid" if not invalid else "invalid",
            "checked_at": _utc_now(),
            "records_checked": len(reports),
            "invalid_records": len(invalid),
            "reports": reports,
        }


oracle_recall_ledger_integrity_engine = RecallLedgerIntegrityEngine()
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.recall_ledger_integrity_engine import (
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
'''

def update_init():
    INIT.parent.mkdir(parents=True, exist_ok=True)
    if INIT.exists():
        content = INIT.read_text(encoding="utf-8")
    else:
        content = ""

    line = "from .recall_ledger_integrity_engine import oracle_recall_ledger_integrity_engine\n"
    if line not in content:
        content += ("\n" if content and not content.endswith("\n") else "") + line

    INIT.write_text(content, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OI-151 INSTALLER")
    print(" Oracle Recall Ledger Integrity Engine")
    print("=" * 40)

    PKG.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MODULE, encoding="utf-8")
    TEST.write_text(TEST_CODE, encoding="utf-8")
    update_init()

    print(f"[OK] Wrote {MOD}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print("\n[DONE] OI-151 installed")
    print("\nRun:")
    print("py test_oi_151_recall_ledger_integrity_engine.py")


if __name__ == "__main__":
    main()