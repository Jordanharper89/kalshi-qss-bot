
"""
OI-132 Q Series Visibility Archive Engine
Read-only Oracle Intelligence module.
"""

from datetime import datetime, timezone
import hashlib
import json


class QSeriesVisibilityArchiveEngine:
    module = "oi_132_qseries_visibility_archive_engine"

    def __init__(self):
        self.last_archive = {}

    def build_archive(self, release_receipt=None):
        release_receipt = release_receipt or {}
        items = [x for x in release_receipt.get("release_receipt_items", []) if isinstance(x, dict)]

        archive_items = []
        for item in items:
            archive_items.append({
                "market": item.get("market"),
                "archive_score": round(self._float(item.get("receipt_score")), 4),
                "archive_tier": item.get("receipt_tier"),
                "release_receipt_rank": int(self._float(item.get("release_receipt_rank"), 0)),
                "release_score": round(self._float(item.get("release_score")), 4),
                "release_tier": item.get("release_tier"),
                "surface_tier": item.get("surface_tier"),
                "dashboard_tier": item.get("dashboard_tier"),
                "transfer_tier": item.get("transfer_tier"),
                "review_conclusion": item.get("review_conclusion"),
                "q_series_visibility": bool(item.get("q_series_visibility")),
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            })

        archive_items.sort(
            key=lambda x: (
                x["release_receipt_rank"] if x["release_receipt_rank"] else 999999,
                -x["archive_score"],
            )
        )

        archive_id = self._hash_record({
            "release_receipt_status": release_receipt.get("release_receipt_status"),
            "release_receipt_confirmed": release_receipt.get("release_receipt_confirmed"),
            "release_ledger_id": release_receipt.get("release_ledger_id"),
            "items": archive_items,
        })

        archive_status = self._archive_status(release_receipt)

        archive = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "input_module": "oi_131_qseries_visibility_release_receipt_engine",
            "archive_id": archive_id,
            "archive_status": archive_status,
            "archive_confirmed": archive_status == "archived",
            "release_receipt_status": release_receipt.get("release_receipt_status"),
            "release_receipt_confirmed": bool(release_receipt.get("release_receipt_confirmed", False)),
            "release_ledger_id": release_receipt.get("release_ledger_id"),
            "integrity_status": release_receipt.get("integrity_status"),
            "integrity_score": round(self._float(release_receipt.get("integrity_score")), 4),
            "archive_count": len(archive_items),
            "archive_items": archive_items,
            "top_archive_items": archive_items[:10],
            "archive_summary": self._summary(archive_id, archive_status, release_receipt, archive_items),
            "oracle_archive_boundaries": [
                "Q Series visibility archive is read-only.",
                "Oracle archive grants no execution permission.",
                "Oracle does not execute.",
                "Oracle does not approve execution.",
                "Q Series owns execution evaluation and decisions.",
            ],
        }

        self.last_archive = archive
        return archive

    def _archive_status(self, receipt):
        if receipt.get("release_receipt_status") == "confirmed" and receipt.get("release_receipt_confirmed") is True:
            return "archived"
        if receipt.get("release_receipt_status") == "confirmed_with_warnings":
            return "archived_with_warnings"
        return "blocked"

    def _summary(self, archive_id, archive_status, receipt, items):
        counts = {}
        for item in items:
            tier = item["archive_tier"]
            counts[tier] = counts.get(tier, 0) + 1

        top = items[0] if items else None

        if archive_status == "archived" and top:
            headline = f"Q Series visibility archive recorded; top archived market is {top['market']}."
        elif archive_status == "archived":
            headline = "Q Series visibility archive recorded with no market items."
        else:
            headline = f"Q Series visibility archive status is {archive_status}; review required."

        return {
            "headline": headline,
            "archive_id": archive_id,
            "archive_status": archive_status,
            "archive_tier_counts": counts,
            "top_market": top["market"] if top else None,
            "top_archive_tier": top["archive_tier"] if top else None,
            "release_ledger_id": receipt.get("release_ledger_id"),
            "execution_allowed": False,
            "execution_owner": "Q Series",
        }

    def _hash_record(self, data):
        payload = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]

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
            "has_archive": bool(self.last_archive),
            "archive_status": self.last_archive.get("archive_status"),
            "archive_confirmed": self.last_archive.get("archive_confirmed", False),
            "archive_count": self.last_archive.get("archive_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


qseries_visibility_archive_engine = QSeriesVisibilityArchiveEngine()
