from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_ledger_integrity_engine.py"
TEST = ROOT / "test_oi_122_oracle_ledger_integrity_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-122 Oracle Ledger Integrity Engine
Read-only Oracle Intelligence module.

Purpose:
- Verify Oracle transfer ledger entries from OI-121.
- Confirm ledger structure, boundary rules, Q Series ownership, and hash integrity.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from datetime import datetime, timezone
import hashlib
import json


class OracleLedgerIntegrityEngine:
    module = "oi_122_oracle_ledger_integrity_engine"

    def __init__(self):
        self.last_integrity = {}

    def verify_ledger(self, ledger_entry=None):
        ledger_entry = ledger_entry or {}

        checks = []
        checks.append(self._check("status_ok", ledger_entry.get("status") == "ok", "Ledger status must be ok."))
        checks.append(self._check("read_only_true", ledger_entry.get("read_only") is True, "Ledger must be read-only."))
        checks.append(self._check("execution_disabled", ledger_entry.get("execution_allowed") is False, "Ledger cannot allow execution."))
        checks.append(self._check("execution_owner_qseries", ledger_entry.get("execution_owner") == "Q Series", "Execution owner must be Q Series."))
        checks.append(self._check("has_ledger_id", bool(str(ledger_entry.get("ledger_entry_id") or "").strip()), "Ledger entry id must exist."))
        checks.append(self._check("has_ledger_items", len(ledger_entry.get("ledger_items", [])) > 0, "Ledger must include items."))
        checks.append(self._check("has_boundaries", len(ledger_entry.get("oracle_boundaries", [])) >= 3, "Oracle boundaries must be present."))

        hash_check = self._verify_hash(ledger_entry)
        checks.append(hash_check)

        checks.extend(self._verify_items(ledger_entry.get("ledger_items", [])))

        passed = len([x for x in checks if x["passed"]])
        total = len(checks)
        failed = total - passed
        integrity_score = round((passed / max(1, total)) * 100, 4)

        report = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "input_module": "oi_121_oracle_transfer_ledger_engine",
            "integrity_score": integrity_score,
            "integrity_status": self._status(integrity_score, failed),
            "passed_checks": passed,
            "failed_checks": failed,
            "total_checks": total,
            "checks": checks,
            "critical_failures": [x for x in checks if not x["passed"] and x["severity"] == "critical"],
            "warnings": [x for x in checks if not x["passed"] and x["severity"] == "warning"],
            "ledger_integrity_confirmed": failed == 0,
            "ledger_entry_id": ledger_entry.get("ledger_entry_id"),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "integrity_summary": self._summary(integrity_score, failed, checks, ledger_entry),
        }

        self.last_integrity = report
        return report

    def _verify_hash(self, ledger_entry):
        expected = str(ledger_entry.get("ledger_entry_id") or "")
        data = {
            "transfer_status": ledger_entry.get("transfer_status"),
            "transfer_ready": ledger_entry.get("transfer_ready"),
            "audit_status": ledger_entry.get("audit_status"),
            "intake_status": ledger_entry.get("intake_status"),
            "items": ledger_entry.get("ledger_items", []),
        }
        calculated = self._hash_record(data)

        return {
            "check": "ledger_hash_matches_content",
            "passed": expected == calculated,
            "severity": "critical",
            "message": "Ledger hash must match deterministic ledger content.",
            "expected": expected,
            "calculated": calculated,
        }

    def _verify_items(self, items):
        checks = []

        if not isinstance(items, list):
            return [self._check("ledger_items_list", False, "ledger_items must be a list.", "critical")]

        seen_ranks = set()
        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                checks.append(self._check(f"item_{idx}_dict", False, "Every ledger item must be a dict.", "critical"))
                continue

            market = str(item.get("market") or "").strip()
            checks.append(self._check(f"item_{idx}_has_market", bool(market), "Each ledger item must include market.", "critical"))
            checks.append(self._check(f"item_{idx}_read_only", item.get("read_only") is True, "Each ledger item must be read-only.", "critical"))
            checks.append(self._check(f"item_{idx}_execution_disabled", item.get("execution_permission_from_oracle") is False, "Oracle must not grant execution permission.", "critical"))
            checks.append(self._check(f"item_{idx}_owner_qseries", item.get("execution_owner") == "Q Series", "Item execution owner must be Q Series.", "critical"))
            checks.append(self._check(f"item_{idx}_visibility_bool", isinstance(item.get("q_series_visibility"), bool), "Q Series visibility must be boolean.", "warning"))

            score = self._float(item.get("transfer_score"), -1)
            checks.append(self._check(f"item_{idx}_score_range", 0 <= score <= 100, "Transfer score must be 0-100.", "critical"))

            tier = str(item.get("transfer_tier") or "")
            checks.append(self._check(f"item_{idx}_tier_valid", tier in {"critical", "high", "elevated", "watch", "blocked"}, "Transfer tier must be valid.", "warning"))

            rank = int(self._float(item.get("transfer_rank"), 0))
            checks.append(self._check(f"item_{idx}_has_rank", rank > 0, "Each ledger item should include transfer rank.", "warning"))
            if rank:
                if rank in seen_ranks:
                    checks.append(self._check(f"item_{idx}_rank_unique", False, "Transfer ranks should be unique.", "warning"))
                seen_ranks.add(rank)

        return checks

    def _hash_record(self, data):
        payload = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]

    def _check(self, name, passed, message, severity="critical"):
        return {
            "check": name,
            "passed": bool(passed),
            "severity": severity,
            "message": message,
        }

    def _status(self, score, failed):
        if failed == 0:
            return "verified"
        if score >= 85:
            return "verified_with_warnings"
        if score >= 65:
            return "needs_review"
        return "failed"

    def _summary(self, score, failed, checks, ledger_entry):
        if failed == 0:
            headline = "Oracle ledger integrity verified; transfer record is intact."
        else:
            headline = f"Oracle ledger integrity found {failed} issue(s); review ledger before downstream use."

        return {
            "headline": headline,
            "integrity_score": score,
            "failed_checks": failed,
            "critical_failure_count": len([x for x in checks if not x["passed"] and x["severity"] == "critical"]),
            "warning_count": len([x for x in checks if not x["passed"] and x["severity"] == "warning"]),
            "ledger_entry_id": ledger_entry.get("ledger_entry_id"),
            "execution_allowed": False,
            "execution_owner": "Q Series",
        }

    def _float(self, value, default=0.0):
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    def diagnostics(self):
        return {
            "module": self.module,
            "status": "ok",
            "has_integrity": bool(self.last_integrity),
            "integrity_score": self.last_integrity.get("integrity_score", 0),
            "ledger_integrity_confirmed": self.last_integrity.get("ledger_integrity_confirmed", False),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_ledger_integrity_engine = OracleLedgerIntegrityEngine()
''', encoding="utf-8")

TEST.write_text(r'''
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
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_ledger_integrity_engine import oracle_ledger_integrity_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-122 INSTALLER")
print(" Oracle Ledger Integrity Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-122 installed")
print()
print("Run:")
print("py test_oi_122_oracle_ledger_integrity_engine.py")