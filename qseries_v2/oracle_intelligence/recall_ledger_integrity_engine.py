"""
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
