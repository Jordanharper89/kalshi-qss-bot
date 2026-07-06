from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "qseries_visibility_release_ledger_integrity_engine.py"
TEST = ROOT / "test_oi_130_qseries_visibility_release_ledger_integrity_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
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
''', encoding="utf-8")

TEST.write_text(r'''
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
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .qseries_visibility_release_ledger_integrity_engine import qseries_visibility_release_ledger_integrity_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-130 INSTALLER")
print(" Q Series Visibility Release Ledger Integrity Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-130 installed")
print()
print("Run:")
print("py test_oi_130_qseries_visibility_release_ledger_integrity_engine.py")