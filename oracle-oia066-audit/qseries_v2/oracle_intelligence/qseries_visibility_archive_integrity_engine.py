
"""
OI-133 Q Series Visibility Archive Integrity Engine

Read-only Oracle Intelligence module.
Validates archived Oracle visibility packets before they are exposed to
Q Series. Oracle remains strictly read-only.
"""

from datetime import datetime, timezone
import hashlib
import json


class QSeriesVisibilityArchiveIntegrityEngine:

    module = "oi_133_qseries_visibility_archive_integrity_engine"

    def __init__(self):
        self.last_report = {}

    def verify_archive(self, archive=None):

        archive = archive or {}

        checks = []

        checks.append(self._check(
            "archive_exists",
            archive != {},
            "Archive payload supplied."
        ))

        checks.append(self._check(
            "read_only",
            archive.get("read_only") is True,
            "Archive must remain read-only."
        ))

        checks.append(self._check(
            "execution_disabled",
            archive.get("execution_allowed") is False,
            "Oracle cannot execute."
        ))

        checks.append(self._check(
            "execution_owner",
            archive.get("execution_owner") == "Q Series",
            "Execution ownership belongs to Q Series."
        ))

        checks.append(self._check(
            "archive_confirmed",
            archive.get("archive_confirmed") is True,
            "Archive confirmation required."
        ))

        checks.append(self._check(
            "archive_id_present",
            bool(archive.get("archive_id")),
            "Archive id exists."
        ))

        items = archive.get("archive_items", [])

        for index, item in enumerate(items, start=1):

            checks.append(self._check(
                f"item_{index}_market",
                bool(item.get("market")),
                "Market exists."
            ))

            checks.append(self._check(
                f"item_{index}_read_only",
                item.get("read_only") is True,
                "Item remains read-only."
            ))

            checks.append(self._check(
                f"item_{index}_visibility",
                item.get("q_series_visibility") is True,
                "Visible to Q Series."
            ))

            checks.append(self._check(
                f"item_{index}_execution",
                item.get("execution_permission_from_oracle") is False,
                "Oracle grants no execution."
            ))

            checks.append(self._check(
                f"item_{index}_owner",
                item.get("execution_owner") == "Q Series",
                "Execution owner verified."
            ))

        passed = len([c for c in checks if c["passed"]])
        failed = len(checks) - passed

        score = round((passed / max(len(checks), 1)) * 100, 2)

        report = {
            "module": self.module,
            "status": "ok",
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "integrity_score": score,
            "integrity_status": (
                "verified"
                if failed == 0
                else "review_required"
            ),
            "passed_checks": passed,
            "failed_checks": failed,
            "total_checks": len(checks),
            "checks": checks,
            "archive_integrity_confirmed": failed == 0,
            "archive_id": archive.get("archive_id"),
            "summary": self._summary(
                score,
                failed,
                archive
            )
        }

        self.last_report = report

        return report

    def _summary(
        self,
        score,
        failed,
        archive
    ):

        if failed == 0:

            headline = (
                "Archive integrity verified for "
                "Q Series."
            )

        else:

            headline = (
                f"Archive integrity found "
                f"{failed} issue(s)."
            )

        return {
            "headline": headline,
            "archive_id": archive.get(
                "archive_id"
            ),
            "integrity_score": score,
            "failed_checks": failed,
            "execution_allowed": False,
            "execution_owner": "Q Series"
        }

    def _check(
        self,
        name,
        passed,
        message
    ):

        return {
            "check": name,
            "passed": bool(passed),
            "message": message
        }

    def diagnostics(self):

        return {
            "module": self.module,
            "status": "ok",
            "has_report": bool(
                self.last_report
            ),
            "integrity_confirmed": (
                self.last_report.get(
                    "archive_integrity_confirmed",
                    False
                )
            ),
            "execution_allowed": False,
            "read_only": True
        }


qseries_visibility_archive_integrity_engine = (
    QSeriesVisibilityArchiveIntegrityEngine()
)
