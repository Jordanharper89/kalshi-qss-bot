
"""
OI-127 Q Series Visibility Surface Validation Engine
Read-only Oracle Intelligence module.

Purpose:
- Validate the final Q Series visibility surface from OI-126.
- Confirm read-only boundaries, card integrity, visibility readiness, and Q Series ownership.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from datetime import datetime, timezone


class QSeriesVisibilitySurfaceValidationEngine:
    module = "oi_127_qseries_visibility_surface_validation_engine"

    def __init__(self):
        self.last_validation = {}

    def validate_surface(self, visibility_surface=None):
        visibility_surface = visibility_surface or {}

        checks = []
        checks.append(self._check("status_ok", visibility_surface.get("status") == "ok", "Surface status must be ok."))
        checks.append(self._check("read_only_true", visibility_surface.get("read_only") is True, "Surface must be read-only."))
        checks.append(self._check("execution_disabled", visibility_surface.get("execution_allowed") is False, "Surface cannot allow execution."))
        checks.append(self._check("owner_qseries", visibility_surface.get("execution_owner") == "Q Series", "Execution owner must be Q Series."))
        checks.append(self._check("surface_visible", visibility_surface.get("surface_status") in {"visible", "visible_with_warnings"}, "Surface must be visible."))
        checks.append(self._check("qseries_ready", visibility_surface.get("q_series_visibility_ready") is True, "Q Series visibility must be ready."))
        checks.append(self._check("has_cards", len(visibility_surface.get("surface_cards", [])) > 0, "Surface must contain cards."))
        checks.append(self._check("has_boundaries", len(visibility_surface.get("oracle_surface_boundaries", [])) >= 3, "Surface boundaries must be declared."))

        checks.extend(self._validate_cards(visibility_surface.get("surface_cards", [])))

        passed = len([x for x in checks if x["passed"]])
        total = len(checks)
        failed = total - passed
        score = round((passed / max(1, total)) * 100, 4)

        report = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "input_module": "oi_126_qseries_visibility_surface_engine",
            "validation_score": score,
            "validation_status": self._status(score, failed),
            "passed_checks": passed,
            "failed_checks": failed,
            "total_checks": total,
            "checks": checks,
            "critical_failures": [x for x in checks if not x["passed"] and x["severity"] == "critical"],
            "warnings": [x for x in checks if not x["passed"] and x["severity"] == "warning"],
            "surface_ready_for_qseries": failed == 0,
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "validation_summary": self._summary(score, failed, checks, visibility_surface),
        }

        self.last_validation = report
        return report

    def _validate_cards(self, cards):
        checks = []

        if not isinstance(cards, list):
            return [self._check("surface_cards_list", False, "surface_cards must be a list.", "critical")]

        seen_ranks = set()
        for idx, card in enumerate(cards, start=1):
            if not isinstance(card, dict):
                checks.append(self._check(f"card_{idx}_dict", False, "Every surface card must be a dict.", "critical"))
                continue

            market = str(card.get("market") or "").strip()
            checks.append(self._check(f"card_{idx}_has_market", bool(market), "Each card must include market.", "critical"))
            checks.append(self._check(f"card_{idx}_read_only", card.get("read_only") is True, "Each card must be read-only.", "critical"))
            checks.append(self._check(f"card_{idx}_execution_disabled", card.get("execution_permission_from_oracle") is False, "Oracle cannot grant execution permission.", "critical"))
            checks.append(self._check(f"card_{idx}_owner_qseries", card.get("execution_owner") == "Q Series", "Card execution owner must be Q Series.", "critical"))
            checks.append(self._check(f"card_{idx}_qseries_visible", card.get("q_series_visibility") is True, "Card must be visible to Q Series.", "critical"))

            score = self._float(card.get("surface_score"), -1)
            checks.append(self._check(f"card_{idx}_score_range", 0 <= score <= 100, "Surface score must be 0-100.", "critical"))

            tier = str(card.get("surface_tier") or "")
            checks.append(self._check(f"card_{idx}_tier_valid", tier in {"critical", "high", "elevated", "watch", "blocked"}, "Surface tier must be valid.", "warning"))

            rank = int(self._float(card.get("surface_rank"), 0))
            checks.append(self._check(f"card_{idx}_has_rank", rank > 0, "Each surface card should include rank.", "warning"))
            if rank:
                if rank in seen_ranks:
                    checks.append(self._check(f"card_{idx}_rank_unique", False, "Surface ranks should be unique.", "warning"))
                seen_ranks.add(rank)

            note = str(card.get("surface_note") or "").strip()
            checks.append(self._check(f"card_{idx}_has_note", bool(note), "Each card should include surface note.", "warning"))

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

    def _summary(self, score, failed, checks, surface):
        if failed == 0:
            headline = "Q Series visibility surface validation passed; surface is ready."
        else:
            headline = f"Q Series visibility surface validation found {failed} issue(s)."

        return {
            "headline": headline,
            "validation_score": score,
            "failed_checks": failed,
            "critical_failure_count": len([x for x in checks if not x["passed"] and x["severity"] == "critical"]),
            "warning_count": len([x for x in checks if not x["passed"] and x["severity"] == "warning"]),
            "surface_status": surface.get("surface_status"),
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
            "surface_ready_for_qseries": self.last_validation.get("surface_ready_for_qseries", False),
            "execution_allowed": False,
            "read_only": True,
        }


qseries_visibility_surface_validation_engine = QSeriesVisibilitySurfaceValidationEngine()
