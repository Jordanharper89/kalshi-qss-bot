
"""
OI-116 Oracle Handoff Validation Engine
Read-only Oracle Intelligence module.

Purpose:
- Validate Oracle handoff packets before downstream Q Series visibility.
- Confirm read-only boundaries, execution ownership, required fields, and item quality.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from datetime import datetime, timezone


class OracleHandoffValidationEngine:
    module = "oi_116_oracle_handoff_validation_engine"

    def __init__(self):
        self.last_validation = {}

    def validate_handoff(self, handoff_packet=None):
        handoff_packet = handoff_packet or {}

        checks = []
        checks.append(self._check("status_ok", handoff_packet.get("status") == "ok", "Handoff status must be ok."))
        checks.append(self._check("read_only_true", handoff_packet.get("read_only") is True, "Oracle handoff must be read-only."))
        checks.append(self._check("execution_disabled", handoff_packet.get("execution_allowed") is False, "Oracle execution must be disabled."))
        checks.append(self._check("execution_owner_qseries", handoff_packet.get("execution_owner") == "Q Series", "Execution owner must be Q Series."))
        checks.append(self._check("has_handoff_items", len(handoff_packet.get("handoff_items", [])) > 0, "Handoff must include items."))
        checks.append(self._check("has_handoff_summary", isinstance(handoff_packet.get("handoff_summary"), dict), "Handoff summary must exist."))
        checks.append(self._check("has_oracle_limits", len(handoff_packet.get("oracle_limits", [])) >= 3, "Oracle limits must be declared."))

        item_checks = self._validate_items(handoff_packet.get("handoff_items", []))
        checks.extend(item_checks)

        passed = len([x for x in checks if x["passed"]])
        failed = len(checks) - passed
        validation_score = round((passed / max(1, len(checks))) * 100, 4)

        report = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "input_module": "oi_115_oracle_intelligence_handoff_engine",
            "validation_score": validation_score,
            "validation_status": self._status(validation_score, failed),
            "passed_checks": passed,
            "failed_checks": failed,
            "total_checks": len(checks),
            "checks": checks,
            "critical_failures": [x for x in checks if not x["passed"] and x["severity"] == "critical"],
            "warnings": [x for x in checks if not x["passed"] and x["severity"] == "warning"],
            "handoff_ready_for_q_series_visibility": failed == 0,
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "validation_summary": self._summary(validation_score, failed, checks),
        }

        self.last_validation = report
        return report

    def _validate_items(self, items):
        checks = []

        if not isinstance(items, list):
            return [self._check("handoff_items_list", False, "handoff_items must be a list.", "critical")]

        seen_ranks = set()
        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                checks.append(self._check(f"item_{idx}_is_dict", False, "Every handoff item must be a dict.", "critical"))
                continue

            market = str(item.get("market") or "").strip()
            checks.append(self._check(f"item_{idx}_has_market", bool(market), "Each item must include market.", "critical"))
            checks.append(self._check(f"item_{idx}_read_only", item.get("read_only") is True, "Each item must be read-only.", "critical"))
            checks.append(self._check(f"item_{idx}_execution_disabled", item.get("execution_allowed") is False, "Each item must disable execution.", "critical"))
            checks.append(self._check(f"item_{idx}_execution_owner", item.get("execution_owner") == "Q Series", "Each item execution owner must be Q Series.", "critical"))

            score = self._float(item.get("handoff_score"), -1)
            checks.append(self._check(f"item_{idx}_score_range", 0 <= score <= 100, "Each handoff score must be 0-100.", "critical"))

            tier = str(item.get("handoff_tier") or "")
            checks.append(self._check(f"item_{idx}_tier_valid", tier in {"critical", "high", "elevated", "watch", "low"}, "Each handoff tier must be valid.", "warning"))

            rank = int(self._float(item.get("handoff_rank"), 0))
            checks.append(self._check(f"item_{idx}_has_rank", rank > 0, "Each item must have handoff rank.", "warning"))
            if rank:
                if rank in seen_ranks:
                    checks.append(self._check(f"item_{idx}_rank_unique", False, "Handoff ranks must be unique.", "warning"))
                seen_ranks.add(rank)

            note = str(item.get("handoff_note") or "").strip()
            checks.append(self._check(f"item_{idx}_has_note", bool(note), "Each item should include handoff note.", "warning"))

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

    def _summary(self, score, failed, checks):
        if failed == 0:
            headline = "Oracle handoff validation passed; packet is ready for Q Series visibility."
        else:
            headline = f"Oracle handoff validation found {failed} issue(s); review before Q Series visibility."

        return {
            "headline": headline,
            "validation_score": score,
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
            "has_validation": bool(self.last_validation),
            "validation_score": self.last_validation.get("validation_score", 0),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_handoff_validation_engine = OracleHandoffValidationEngine()
