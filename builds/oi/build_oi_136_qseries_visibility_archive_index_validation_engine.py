from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "qseries_visibility_archive_index_validation_engine.py"
TEST = ROOT / "test_oi_136_qseries_visibility_archive_index_validation_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-136 Q Series Visibility Archive Index Validation Engine

Read-only Oracle Intelligence module.

Purpose:
- Validate the Q Series visibility archive index from OI-135.
- Confirm index structure, market map, tier map, ranking, read-only boundaries,
  and Q Series execution ownership.
- Oracle does not execute.
- Q Series owns execution.
"""

from datetime import datetime, timezone


class QSeriesVisibilityArchiveIndexValidationEngine:
    module = "oi_136_qseries_visibility_archive_index_validation_engine"

    def __init__(self):
        self.last_validation = {}

    def validate_index(self, archive_index=None):
        archive_index = archive_index or {}

        checks = []

        checks.append(self._check(
            "status_ok",
            archive_index.get("status") == "ok",
            "Archive index status must be ok.",
            "critical",
        ))

        checks.append(self._check(
            "read_only_true",
            archive_index.get("read_only") is True,
            "Archive index must be read-only.",
            "critical",
        ))

        checks.append(self._check(
            "execution_disabled",
            archive_index.get("execution_allowed") is False,
            "Oracle archive index cannot allow execution.",
            "critical",
        ))

        checks.append(self._check(
            "owner_qseries",
            archive_index.get("execution_owner") == "Q Series",
            "Execution owner must be Q Series.",
            "critical",
        ))

        checks.append(self._check(
            "index_confirmed",
            archive_index.get("index_confirmed") is True,
            "Archive index must be confirmed.",
            "critical",
        ))

        checks.append(self._check(
            "has_index_id",
            bool(str(archive_index.get("index_id") or "").strip()),
            "Archive index id must exist.",
            "critical",
        ))

        checks.append(self._check(
            "has_index_items",
            len(archive_index.get("index_items", [])) > 0,
            "Archive index must contain index items.",
            "critical",
        ))

        checks.append(self._check(
            "has_tier_index",
            isinstance(archive_index.get("tier_index"), dict),
            "Archive index must include tier_index.",
            "critical",
        ))

        checks.append(self._check(
            "has_market_index",
            isinstance(archive_index.get("market_index"), dict),
            "Archive index must include market_index.",
            "critical",
        ))

        checks.append(self._check(
            "has_boundaries",
            len(archive_index.get("oracle_index_boundaries", [])) >= 3,
            "Oracle index boundaries must be declared.",
            "critical",
        ))

        checks.extend(self._validate_items(
            archive_index.get("index_items", []),
            archive_index.get("market_index", {}),
            archive_index.get("tier_index", {}),
        ))

        passed = len([x for x in checks if x["passed"]])
        total = len(checks)
        failed = total - passed
        validation_score = round((passed / max(1, total)) * 100, 4)

        report = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "input_module": "oi_135_qseries_visibility_archive_index_engine",
            "validation_score": validation_score,
            "validation_status": self._status(validation_score, failed),
            "passed_checks": passed,
            "failed_checks": failed,
            "total_checks": total,
            "checks": checks,
            "critical_failures": [
                x for x in checks
                if not x["passed"] and x["severity"] == "critical"
            ],
            "warnings": [
                x for x in checks
                if not x["passed"] and x["severity"] == "warning"
            ],
            "archive_index_validated": failed == 0,
            "index_id": archive_index.get("index_id"),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "validation_summary": self._summary(
                validation_score,
                failed,
                checks,
                archive_index,
            ),
        }

        self.last_validation = report
        return report

    def _validate_items(self, items, market_index, tier_index):
        checks = []

        if not isinstance(items, list):
            return [
                self._check(
                    "index_items_list",
                    False,
                    "index_items must be a list.",
                    "critical",
                )
            ]

        seen_ranks = set()
        seen_markets = set()

        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                checks.append(self._check(
                    f"item_{idx}_dict",
                    False,
                    "Every index item must be a dict.",
                    "critical",
                ))
                continue

            market = str(item.get("market") or "").strip()
            rank = int(self._float(item.get("index_rank"), 0))
            score = self._float(item.get("index_score"), -1)
            tier = str(item.get("index_tier") or "")

            checks.append(self._check(
                f"item_{idx}_has_market",
                bool(market),
                "Each index item must include market.",
                "critical",
            ))

            checks.append(self._check(
                f"item_{idx}_read_only",
                item.get("read_only") is True,
                "Each index item must be read-only.",
                "critical",
            ))

            checks.append(self._check(
                f"item_{idx}_execution_disabled",
                item.get("execution_permission_from_oracle") is False,
                "Oracle cannot grant execution permission.",
                "critical",
            ))

            checks.append(self._check(
                f"item_{idx}_owner_qseries",
                item.get("execution_owner") == "Q Series",
                "Item execution owner must be Q Series.",
                "critical",
            ))

            checks.append(self._check(
                f"item_{idx}_qseries_visible",
                item.get("q_series_visibility") is True,
                "Indexed item must be visible to Q Series.",
                "critical",
            ))

            checks.append(self._check(
                f"item_{idx}_score_range",
                0 <= score <= 100,
                "Index score must be 0-100.",
                "critical",
            ))

            checks.append(self._check(
                f"item_{idx}_tier_valid",
                tier in {"critical", "high", "elevated", "watch", "blocked", "low"},
                "Index tier must be valid.",
                "warning",
            ))

            checks.append(self._check(
                f"item_{idx}_has_rank",
                rank > 0,
                "Each index item must include index rank.",
                "critical",
            ))

            if rank:
                checks.append(self._check(
                    f"item_{idx}_rank_unique",
                    rank not in seen_ranks,
                    "Index ranks must be unique.",
                    "critical",
                ))
                seen_ranks.add(rank)

            if market:
                checks.append(self._check(
                    f"item_{idx}_market_unique",
                    market not in seen_markets,
                    "Index markets should be unique.",
                    "warning",
                ))
                seen_markets.add(market)

                checks.append(self._check(
                    f"item_{idx}_market_index_present",
                    market in market_index,
                    "Market must appear in market_index.",
                    "critical",
                ))

            if tier:
                tier_rows = tier_index.get(tier, [])
                tier_markets = [
                    str(row.get("market"))
                    for row in tier_rows
                    if isinstance(row, dict)
                ]
                checks.append(self._check(
                    f"item_{idx}_tier_index_present",
                    market in tier_markets,
                    "Market must appear in matching tier_index bucket.",
                    "warning",
                ))

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

    def _summary(self, score, failed, checks, archive_index):
        if failed == 0:
            headline = "Q Series visibility archive index validation passed."
        else:
            headline = f"Q Series visibility archive index validation found {failed} issue(s)."

        return {
            "headline": headline,
            "validation_score": score,
            "failed_checks": failed,
            "critical_failure_count": len([
                x for x in checks
                if not x["passed"] and x["severity"] == "critical"
            ]),
            "warning_count": len([
                x for x in checks
                if not x["passed"] and x["severity"] == "warning"
            ]),
            "index_id": archive_index.get("index_id"),
            "index_status": archive_index.get("index_status"),
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
            "archive_index_validated": self.last_validation.get(
                "archive_index_validated",
                False,
            ),
            "execution_allowed": False,
            "read_only": True,
        }


qseries_visibility_archive_index_validation_engine = (
    QSeriesVisibilityArchiveIndexValidationEngine()
)
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.qseries_visibility_archive_index_validation_engine import (
    qseries_visibility_archive_index_validation_engine,
)


def test_oi_136_qseries_visibility_archive_index_validation_engine():
    archive_index = {
        "status": "ok",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "index_id": "index-001",
        "index_status": "indexed",
        "index_confirmed": True,
        "oracle_index_boundaries": [
            "Q Series visibility archive index is read-only.",
            "Oracle does not execute.",
            "Q Series owns execution evaluation and decisions.",
        ],
        "index_items": [
            {
                "market": "CRYPTO",
                "index_rank": 1,
                "index_score": 100.0,
                "index_tier": "critical",
                "archive_score": 100.0,
                "archive_tier": "critical",
                "review_conclusion": "high_confidence_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
            {
                "market": "NASDAQ",
                "index_rank": 2,
                "index_score": 95.4,
                "index_tier": "high",
                "archive_score": 95.4,
                "archive_tier": "high",
                "review_conclusion": "confirmed_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
        ],
        "tier_index": {
            "critical": [
                {
                    "market": "CRYPTO",
                    "index_rank": 1,
                    "index_score": 100.0,
                }
            ],
            "high": [
                {
                    "market": "NASDAQ",
                    "index_rank": 2,
                    "index_score": 95.4,
                }
            ],
        },
        "market_index": {
            "CRYPTO": {
                "index_rank": 1,
                "index_score": 100.0,
                "index_tier": "critical",
                "q_series_visibility": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            },
            "NASDAQ": {
                "index_rank": 2,
                "index_score": 95.4,
                "index_tier": "high",
                "q_series_visibility": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            },
        },
    }

    report = (
        qseries_visibility_archive_index_validation_engine.validate_index(
            archive_index
        )
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["validation_status"] == "validated"
    assert report["archive_index_validated"] is True
    assert report["failed_checks"] == 0
    assert report["validation_score"] == 100.0

    diag = qseries_visibility_archive_index_validation_engine.diagnostics()

    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["archive_index_validated"] is True

    print("[PASS] OI-136 Q Series Visibility Archive Index Validation Engine")
    print({
        "validation_score": report["validation_score"],
        "validation_status": report["validation_status"],
        "validated": report["archive_index_validated"],
        "summary": report["validation_summary"],
    })


if __name__ == "__main__":
    test_oi_136_qseries_visibility_archive_index_validation_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = (
    "from .qseries_visibility_archive_index_validation_engine "
    "import qseries_visibility_archive_index_validation_engine\n"
)

if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-136 INSTALLER")
print(" Q Series Visibility Archive Index Validation Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-136 installed")
print()
print("Run:")
print("py test_oi_136_qseries_visibility_archive_index_validation_engine.py")