
"""
OI-130 Q Series Visibility Release Ledger Integrity Engine
Read-only Oracle Intelligence module.

Purpose:
- Verify OI-129 Q Series visibility release ledger integrity.
- Confirm deterministic ledger hash, release item structure, read-only boundaries,
  and Q Series execution ownership.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from datetime import datetime, timezone
import hashlib
import json


class QSeriesVisibilityReleaseLedgerIntegrityEngine:
    module = "oi_130_qseries_visibility_release_ledger_integrity_engine"

    def __init__(self):
        self.last_integrity = {}

    def verify_release_ledger(self, release_ledger=None):
        release_ledger = release_ledger or {}

        checks = []
        checks.append(self._check("status_ok", release_ledger.get("status") == "ok", "Release ledger status must be ok."))
        checks.append(self._check("read_only_true", release_ledger.get("read_only") is True, "Release ledger must be read-only."))
        checks.append(self._check("execution_disabled", release_ledger.get("execution_allowed") is False, "Release ledger cannot allow execution."))
        checks.append(self._check("owner_qseries", release_ledger.get("execution_owner") == "Q Series", "Execution owner must be Q Series."))
        checks.append(self._check("release_confirmed", release_ledger.get("release_confirmed") is True, "Release must be confirmed."))
        checks.append(self._check("has_ledger_id", bool(str(release_ledger.get("release_ledger_id") or "").strip()), "Release ledger id must exist."))
        checks.append(self._check("has_items", len(release_ledger.get("release_ledger_items", [])) > 0, "Release ledger must include items."))
        checks.append(self._check("has_boundaries", len(release_ledger.get("oracle_release_ledger_boundaries", [])) >= 3, "Release ledger boundaries must be declared."))

        checks.append(self._verify_hash(release_ledger))
        checks.extend(self._verify_items(release_ledger.get("release_ledger_items", [])))

        passed = len([x for x in checks if x["passed"]])
        total = len(checks)
        failed = total - passed
        score = round((passed / max(1, total)) * 100, 4)

        report = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "input_module": "oi_129_qseries_visibility_release_ledger_engine",
            "integrity_score": score,
            "integrity_status": self._status(score, failed),
            "passed_checks": passed,
            "failed_checks": failed,
            "total_checks": total,
            "checks": checks,
            "critical_failures": [x for x in checks if not x["passed"] and x["severity"] == "critical"],
            "warnings": [x for x in checks if not x["passed"] and x["severity"] == "warning"],
            "release_ledger_integrity_confirmed": failed == 0,
            "release_ledger_id": release_ledger.get("release_ledger_id"),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "integrity_summary": self._summary(score, failed, checks, release_ledger),
        }

        self.last_integrity = report
        return report

    def _verify_hash(self, release_ledger):
        expected = str(release_ledger.get("release_ledger_id") or "")
        data = {
            "release_status": release_ledger.get("release_status"),
            "release_confirmed": release_ledger.get("release_confirmed"),
            "surface_status": release_ledger.get("surface_status"),
            "validation_status": release_ledger.get("validation_status"),
            "items": release_ledger.get("release_ledger_items", []),
        }
        calculated = self._hash_record(data)

        return {
            "check": "release_ledger_hash_matches_content",
            "passed": expected == calculated,
            "severity": "critical",
            "message": "Release ledger hash must match deterministic release ledger content.",
            "expected": expected,
            "calculated": calculated,
        }

    def _verify_items(self, items):
        checks = []

        if not isinstance(items, list):
            return [self._check("release_items_list", False, "release_ledger_items must be a list.", "critical")]

        seen_ranks = set()
        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                checks.append(self._check(f"item_{idx}_dict", False, "Every release ledger item must be a dict.", "critical"))
                continue

            market = str(item.get("market") or "").strip()
            checks.append(self._check(f"item_{idx}_has_market", bool(market), "Each release ledger item must include market.", "critical"))
            checks.append(self._check(f"item_{idx}_read_only", item.get("read_only") is True, "Each release ledger item must be read-only.", "critical"))
            checks.append(self._check(f"item_{idx}_execution_disabled", item.get("execution_permission_from_oracle") is False, "Oracle cannot grant execution permission.", "critical"))
            checks.append(self._check(f"item_{idx}_owner_qseries", item.get("execution_owner") == "Q Series", "Item execution owner must be Q Series.", "critical"))
            checks.append(self._check(f"item_{idx}_qseries_visible", item.get("q_series_visibility") is True, "Released item must be visible to Q Series.", "critical"))

            score = self._float(item.get("release_score"), -1)
            checks.append(self._check(f"item_{idx}_score_range", 0 <= score <= 100, "Release score must be 0-100.", "critical"))

            tier = str(item.get("release_tier") or "")
            checks.append(self._check(f"item_{idx}_tier_valid", tier in {"critical", "high", "elevated", "watch", "blocked"}, "Release tier must be valid.", "warning"))

            rank = int(self._float(item.get("release_rank"), 0))
            checks.append(self._check(f"item_{idx}_has_rank", rank > 0, "Each release ledger item should include release rank.", "warning"))
            if rank:
                if rank in seen_ranks:
                    checks.append(self._check(f"item_{idx}_rank_unique", False, "Release ranks should be unique.", "warning"))
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

    def _summary(self, score, failed, checks, release_ledger):
        if failed == 0:
            headline = "Q Series visibility release ledger integrity verified."
        else:
            headline = f"Q Series visibility release ledger integrity found {failed} issue(s)."

        return {
            "headline": headline,
            "integrity_score": score,
            "failed_checks": failed,
            "critical_failure_count": len([x for x in checks if not x["passed"] and x["severity"] == "critical"]),
            "warning_count": len([x for x in checks if not x["passed"] and x["severity"] == "warning"]),
            "release_ledger_id": release_ledger.get("release_ledger_id"),
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
            "release_ledger_integrity_confirmed": self.last_integrity.get("release_ledger_integrity_confirmed", False),
            "execution_allowed": False,
            "read_only": True,
        }


qseries_visibility_release_ledger_integrity_engine = QSeriesVisibilityReleaseLedgerIntegrityEngine()
