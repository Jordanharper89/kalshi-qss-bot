from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_transfer_dashboard_validation_engine.py"
TEST = ROOT / "test_oi_125_oracle_transfer_dashboard_validation_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-125 Oracle Transfer Dashboard Validation Engine
Read-only Oracle Intelligence module.

Purpose:
- Validate OI-124 Oracle transfer dashboard output.
- Confirm dashboard visibility, card integrity, read-only boundaries, and Q Series execution ownership.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from datetime import datetime, timezone


class OracleTransferDashboardValidationEngine:
    module = "oi_125_oracle_transfer_dashboard_validation_engine"

    def __init__(self):
        self.last_validation = {}

    def validate_dashboard(self, dashboard=None):
        dashboard = dashboard or {}

        checks = []
        checks.append(self._check("status_ok", dashboard.get("status") == "ok", "Dashboard status must be ok."))
        checks.append(self._check("read_only_true", dashboard.get("read_only") is True, "Dashboard must be read-only."))
        checks.append(self._check("execution_disabled", dashboard.get("execution_allowed") is False, "Dashboard cannot allow execution."))
        checks.append(self._check("owner_qseries", dashboard.get("execution_owner") == "Q Series", "Execution owner must be Q Series."))
        checks.append(self._check("dashboard_confirmed", dashboard.get("dashboard_status") in {"confirmed_visible", "visible_with_warnings"}, "Dashboard must be visible or warning-visible."))
        checks.append(self._check("receipt_confirmed", dashboard.get("receipt_confirmed") is True, "Receipt must be confirmed."))
        checks.append(self._check("ledger_integrity_confirmed", dashboard.get("ledger_integrity_confirmed") is True, "Ledger integrity must be confirmed."))
        checks.append(self._check("has_cards", len(dashboard.get("dashboard_cards", [])) > 0, "Dashboard must contain cards."))
        checks.append(self._check("has_boundaries", len(dashboard.get("oracle_dashboard_boundaries", [])) >= 3, "Dashboard boundaries must be present."))

        checks.extend(self._validate_cards(dashboard.get("dashboard_cards", [])))

        passed = len([x for x in checks if x["passed"]])
        total = len(checks)
        failed = total - passed
        score = round((passed / max(1, total)) * 100, 4)

        report = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "input_module": "oi_124_oracle_transfer_dashboard_engine",
            "validation_score": score,
            "validation_status": self._status(score, failed),
            "passed_checks": passed,
            "failed_checks": failed,
            "total_checks": total,
            "checks": checks,
            "critical_failures": [x for x in checks if not x["passed"] and x["severity"] == "critical"],
            "warnings": [x for x in checks if not x["passed"] and x["severity"] == "warning"],
            "dashboard_ready": failed == 0,
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "validation_summary": self._summary(score, failed, checks, dashboard),
        }

        self.last_validation = report
        return report

    def _validate_cards(self, cards):
        checks = []

        if not isinstance(cards, list):
            return [self._check("cards_list", False, "dashboard_cards must be a list.", "critical")]

        seen_ranks = set()
        for idx, card in enumerate(cards, start=1):
            if not isinstance(card, dict):
                checks.append(self._check(f"card_{idx}_dict", False, "Every dashboard card must be a dict.", "critical"))
                continue

            market = str(card.get("market") or "").strip()
            checks.append(self._check(f"card_{idx}_has_market", bool(market), "Each card must include market.", "critical"))
            checks.append(self._check(f"card_{idx}_read_only", card.get("read_only") is True, "Each card must be read-only.", "critical"))
            checks.append(self._check(f"card_{idx}_execution_disabled", card.get("execution_permission_from_oracle") is False, "Oracle cannot grant execution permission.", "critical"))
            checks.append(self._check(f"card_{idx}_owner_qseries", card.get("execution_owner") == "Q Series", "Card execution owner must be Q Series.", "critical"))
            checks.append(self._check(f"card_{idx}_visibility_bool", isinstance(card.get("q_series_visibility"), bool), "Q Series visibility must be boolean.", "warning"))

            score = self._float(card.get("dashboard_score"), -1)
            checks.append(self._check(f"card_{idx}_score_range", 0 <= score <= 100, "Dashboard score must be 0-100.", "critical"))

            tier = str(card.get("dashboard_tier") or "")
            checks.append(self._check(f"card_{idx}_tier_valid", tier in {"critical", "high", "elevated", "watch", "blocked"}, "Dashboard tier must be valid.", "warning"))

            rank = int(self._float(card.get("dashboard_rank"), 0))
            checks.append(self._check(f"card_{idx}_has_rank", rank > 0, "Each dashboard card should include rank.", "warning"))
            if rank:
                if rank in seen_ranks:
                    checks.append(self._check(f"card_{idx}_rank_unique", False, "Dashboard ranks should be unique.", "warning"))
                seen_ranks.add(rank)

            note = str(card.get("dashboard_note") or "").strip()
            checks.append(self._check(f"card_{idx}_has_note", bool(note), "Each card should include dashboard note.", "warning"))

        return checks

    def _check(self, name, passed, message, severity="critical"):
        return {
            "check": name,
            "passed": bool(passed),
            "severity": severity,
            "message": message,
        }

    def _status(self, score, failed):
        if failed == 0:
            return "validated"
        if score >= 85:
            return "validated_with_warnings"
        if score >= 65:
            return "needs_review"
        return "invalid"

    def _summary(self, score, failed, checks, dashboard):
        if failed == 0:
            headline = "Oracle transfer dashboard validation passed; dashboard is ready."
        else:
            headline = f"Oracle transfer dashboard validation found {failed} issue(s)."

        return {
            "headline": headline,
            "validation_score": score,
            "failed_checks": failed,
            "critical_failure_count": len([x for x in checks if not x["passed"] and x["severity"] == "critical"]),
            "warning_count": len([x for x in checks if not x["passed"] and x["severity"] == "warning"]),
            "dashboard_status": dashboard.get("dashboard_status"),
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
            "has_validation": bool(self.last_validation),
            "validation_score": self.last_validation.get("validation_score", 0),
            "dashboard_ready": self.last_validation.get("dashboard_ready", False),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_transfer_dashboard_validation_engine = OracleTransferDashboardValidationEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.oracle_transfer_dashboard_validation_engine import oracle_transfer_dashboard_validation_engine


def test_oi_125_oracle_transfer_dashboard_validation_engine():
    dashboard = {
        "status": "ok",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "dashboard_status": "confirmed_visible",
        "receipt_confirmed": True,
        "ledger_integrity_confirmed": True,
        "transfer_ready": True,
        "card_count": 2,
        "oracle_dashboard_boundaries": [
            "Oracle transfer dashboard is read-only.",
            "Oracle does not execute.",
            "Q Series owns execution evaluation and decisions.",
        ],
        "dashboard_cards": [
            {
                "market": "CRYPTO",
                "dashboard_rank": 1,
                "dashboard_score": 100.0,
                "dashboard_tier": "critical",
                "receipt_tier": "critical",
                "transfer_tier": "critical",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
                "dashboard_note": "CRYPTO dashboard tier is critical.",
            },
            {
                "market": "NASDAQ",
                "dashboard_rank": 2,
                "dashboard_score": 100.0,
                "dashboard_tier": "critical",
                "receipt_tier": "critical",
                "transfer_tier": "critical",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
                "dashboard_note": "NASDAQ dashboard tier is critical.",
            },
        ],
    }

    report = oracle_transfer_dashboard_validation_engine.validate_dashboard(dashboard)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["validation_status"] == "validated"
    assert report["dashboard_ready"] is True
    assert report["failed_checks"] == 0
    assert report["validation_score"] == 100.0

    diag = oracle_transfer_dashboard_validation_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["dashboard_ready"] is True

    print("[PASS] OI-125 Oracle Transfer Dashboard Validation Engine")
    print({
        "validation_score": report["validation_score"],
        "validation_status": report["validation_status"],
        "dashboard_ready": report["dashboard_ready"],
        "summary": report["validation_summary"],
    })


if __name__ == "__main__":
    test_oi_125_oracle_transfer_dashboard_validation_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_transfer_dashboard_validation_engine import oracle_transfer_dashboard_validation_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-125 INSTALLER")
print(" Oracle Transfer Dashboard Validation Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-125 installed")
print()
print("Run:")
print("py test_oi_125_oracle_transfer_dashboard_validation_engine.py")