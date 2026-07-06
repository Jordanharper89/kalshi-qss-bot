from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "qseries_intake_audit_engine.py"
TEST = ROOT / "test_oi_119_qseries_intake_audit_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-119 Q Series Intake Audit Engine
Read-only Oracle Intelligence module.

Purpose:
- Audit Q Series intake packets from OI-118.
- Confirm Oracle read-only boundaries, execution ownership, visibility readiness,
  item integrity, and downstream-safe structure.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from datetime import datetime, timezone


class QSeriesIntakeAuditEngine:
    module = "oi_119_qseries_intake_audit_engine"

    def __init__(self):
        self.last_audit = {}

    def audit_intake_packet(self, intake_packet=None):
        intake_packet = intake_packet or {}

        checks = []
        checks.append(self._check("status_ok", intake_packet.get("status") == "ok", "Intake packet status must be ok."))
        checks.append(self._check("read_only_true", intake_packet.get("read_only") is True, "Intake packet must be read-only."))
        checks.append(self._check("execution_disabled", intake_packet.get("execution_allowed") is False, "Oracle intake cannot allow execution."))
        checks.append(self._check("execution_owner_qseries", intake_packet.get("execution_owner") == "Q Series", "Execution owner must be Q Series."))
        checks.append(self._check("visibility_ready", intake_packet.get("q_series_visibility_ready") is True, "Q Series visibility must be ready."))
        checks.append(self._check("intake_status_ready", intake_packet.get("intake_status") in {"ready", "ready_with_warnings"}, "Intake status must be ready or ready_with_warnings."))
        checks.append(self._check("has_boundary_notice", len(intake_packet.get("oracle_boundary_notice", [])) >= 3, "Oracle boundary notice must be present."))

        item_checks = self._audit_items(intake_packet.get("intake_items", []))
        checks.extend(item_checks)

        passed = len([x for x in checks if x["passed"]])
        total = len(checks)
        failed = total - passed
        audit_score = round((passed / max(1, total)) * 100, 4)

        audit = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "input_module": "oi_118_qseries_intake_packet_engine",
            "audit_score": audit_score,
            "audit_status": self._audit_status(audit_score, failed),
            "passed_checks": passed,
            "failed_checks": failed,
            "total_checks": total,
            "checks": checks,
            "critical_failures": [x for x in checks if not x["passed"] and x["severity"] == "critical"],
            "warnings": [x for x in checks if not x["passed"] and x["severity"] == "warning"],
            "q_series_safe_to_view": failed == 0,
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "audit_summary": self._summary(audit_score, failed, checks),
        }

        self.last_audit = audit
        return audit

    def _audit_items(self, items):
        checks = []

        if not isinstance(items, list):
            return [self._check("intake_items_list", False, "intake_items must be a list.", "critical")]

        seen_ranks = set()
        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                checks.append(self._check(f"item_{idx}_dict", False, "Every intake item must be a dict.", "critical"))
                continue

            market = str(item.get("market") or "").strip()
            checks.append(self._check(f"item_{idx}_has_market", bool(market), "Each intake item must include market.", "critical"))
            checks.append(self._check(f"item_{idx}_read_only", item.get("read_only") is True, "Each intake item must be read-only.", "critical"))
            checks.append(self._check(f"item_{idx}_execution_disabled", item.get("execution_permission_from_oracle") is False, "Oracle must not grant execution permission.", "critical"))
            checks.append(self._check(f"item_{idx}_owner_qseries", item.get("execution_owner") == "Q Series", "Item execution owner must be Q Series.", "critical"))
            checks.append(self._check(f"item_{idx}_visibility", item.get("q_series_visibility") is True, "Item must be visible to Q Series.", "critical"))

            score = self._float(item.get("intake_score"), -1)
            checks.append(self._check(f"item_{idx}_score_range", 0 <= score <= 100, "Intake score must be 0-100.", "critical"))

            tier = str(item.get("intake_tier") or "")
            checks.append(self._check(f"item_{idx}_tier_valid", tier in {"critical", "high", "elevated", "watch", "blocked"}, "Intake tier must be valid.", "warning"))

            rank = int(self._float(item.get("intake_rank"), 0))
            checks.append(self._check(f"item_{idx}_has_rank", rank > 0, "Each intake item should include rank.", "warning"))
            if rank:
                if rank in seen_ranks:
                    checks.append(self._check(f"item_{idx}_rank_unique", False, "Intake ranks should be unique.", "warning"))
                seen_ranks.add(rank)

            note = str(item.get("intake_note") or "").strip()
            checks.append(self._check(f"item_{idx}_has_note", bool(note), "Each intake item should include note.", "warning"))

        return checks

    def _check(self, name, passed, message, severity="critical"):
        return {
            "check": name,
            "passed": bool(passed),
            "severity": severity,
            "message": message,
        }

    def _audit_status(self, audit_score, failed):
        if failed == 0:
            return "passed"
        if audit_score >= 85:
            return "passed_with_warnings"
        if audit_score >= 65:
            return "needs_review"
        return "failed"

    def _summary(self, audit_score, failed, checks):
        if failed == 0:
            headline = "Q Series intake audit passed; packet is safe for Q Series visibility."
        else:
            headline = f"Q Series intake audit found {failed} issue(s); review before visibility."

        return {
            "headline": headline,
            "audit_score": audit_score,
            "failed_checks": failed,
            "critical_failure_count": len([x for x in checks if not x["passed"] and x["severity"] == "critical"]),
            "warning_count": len([x for x in checks if not x["passed"] and x["severity"] == "warning"]),
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
            "has_audit": bool(self.last_audit),
            "audit_score": self.last_audit.get("audit_score", 0),
            "q_series_safe_to_view": self.last_audit.get("q_series_safe_to_view", False),
            "execution_allowed": False,
            "read_only": True,
        }


qseries_intake_audit_engine = QSeriesIntakeAuditEngine()
''', encoding="utf-8")

TEST.write_text(r'''
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
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .qseries_intake_audit_engine import qseries_intake_audit_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-119 INSTALLER")
print(" Q Series Intake Audit Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-119 installed")
print()
print("Run:")
print("py test_oi_119_qseries_intake_audit_engine.py")