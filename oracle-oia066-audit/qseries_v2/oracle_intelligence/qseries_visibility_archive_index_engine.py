
"""
OI-135 Q Series Visibility Archive Index Engine

Read-only Oracle Intelligence module.

Purpose:
- Build an index from confirmed Q Series visibility archive receipts.
- Organize archived markets by tier, rank, score, and receipt reference.
- Preserve Oracle read-only boundaries.
- Oracle does not execute.
- Q Series owns execution.
"""

from datetime import datetime, timezone
import hashlib
import json


class QSeriesVisibilityArchiveIndexEngine:
    module = "oi_135_qseries_visibility_archive_index_engine"

    def __init__(self):
        self.last_index = {}

    def build_index(self, archive_receipt=None):
        archive_receipt = archive_receipt or {}

        receipt_items = [
            item for item in archive_receipt.get("receipt_items", [])
            if isinstance(item, dict)
        ]

        if not receipt_items:
            receipt_items = [
                item for item in archive_receipt.get("archive_receipt_items", [])
                if isinstance(item, dict)
            ]

        index_items = []

        for item in receipt_items:
            market = str(item.get("market") or "").strip()
            if not market:
                continue

            score = self._float(
                item.get("archive_receipt_score", item.get("receipt_score", 0.0))
            )

            tier = (
                item.get("archive_receipt_tier")
                or item.get("receipt_tier")
                or self._tier(score)
            )

            index_items.append({
                "market": market,
                "index_score": round(score, 4),
                "index_tier": tier,
                "archive_receipt_rank": int(
                    self._float(
                        item.get("archive_receipt_rank", item.get("receipt_rank", 0))
                    )
                ),
                "archive_score": round(
                    self._float(item.get("archive_score", score)),
                    4,
                ),
                "archive_tier": item.get("archive_tier"),
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

        index_items.sort(
            key=lambda item: (
                -item["index_score"],
                item["archive_receipt_rank"]
                if item["archive_receipt_rank"]
                else 999999,
                item["market"],
            )
        )

        for idx, item in enumerate(index_items, start=1):
            item["index_rank"] = idx

        archive_id = archive_receipt.get("archive_id")
        receipt_id = (
            archive_receipt.get("receipt_id")
            or archive_receipt.get("archive_receipt_id")
        )

        index_id = self._hash_record({
            "archive_id": archive_id,
            "receipt_id": receipt_id,
            "archive_receipt_status": archive_receipt.get("archive_receipt_status"),
            "archive_receipt_confirmed": archive_receipt.get("archive_receipt_confirmed"),
            "items": index_items,
        })

        index_status = self._index_status(archive_receipt)

        report = {
            "module": self.module,
            "status": "ok",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "input_module": "oi_134_qseries_visibility_archive_receipt_engine",
            "index_id": index_id,
            "index_status": index_status,
            "index_confirmed": index_status == "indexed",
            "archive_id": archive_id,
            "receipt_id": receipt_id,
            "archive_receipt_status": archive_receipt.get("archive_receipt_status"),
            "archive_receipt_confirmed": bool(
                archive_receipt.get("archive_receipt_confirmed", False)
            ),
            "index_count": len(index_items),
            "index_items": index_items,
            "top_index_items": index_items[:10],
            "tier_index": self._tier_index(index_items),
            "market_index": self._market_index(index_items),
            "index_summary": self._summary(index_id, index_status, archive_receipt, index_items),
            "oracle_index_boundaries": [
                "Q Series visibility archive index is read-only.",
                "Oracle index grants no execution permission.",
                "Oracle does not execute.",
                "Oracle does not approve execution.",
                "Q Series owns execution evaluation and decisions.",
            ],
        }

        self.last_index = report
        return report

    def _index_status(self, archive_receipt):
        if (
            archive_receipt.get("archive_receipt_status") == "confirmed"
            and archive_receipt.get("archive_receipt_confirmed") is True
        ):
            return "indexed"

        if archive_receipt.get("archive_receipt_status") == "confirmed_with_warnings":
            return "indexed_with_warnings"

        if archive_receipt.get("receipt_confirmed") is True:
            return "indexed"

        return "blocked"

    def _tier_index(self, items):
        out = {}
        for item in items:
            tier = item.get("index_tier") or "unknown"
            out.setdefault(tier, [])
            out[tier].append({
                "market": item["market"],
                "index_rank": item["index_rank"],
                "index_score": item["index_score"],
            })
        return out

    def _market_index(self, items):
        out = {}
        for item in items:
            out[item["market"]] = {
                "index_rank": item["index_rank"],
                "index_score": item["index_score"],
                "index_tier": item["index_tier"],
                "q_series_visibility": item["q_series_visibility"],
                "execution_allowed": False,
                "execution_owner": "Q Series",
            }
        return out

    def _summary(self, index_id, index_status, archive_receipt, items):
        counts = {}
        for item in items:
            tier = item["index_tier"]
            counts[tier] = counts.get(tier, 0) + 1

        top = items[0] if items else None

        if index_status == "indexed" and top:
            headline = f"Q Series visibility archive index built; top indexed market is {top['market']}."
        elif index_status == "indexed":
            headline = "Q Series visibility archive index built with no market items."
        else:
            headline = f"Q Series visibility archive index status is {index_status}; review required."

        return {
            "headline": headline,
            "index_id": index_id,
            "index_status": index_status,
            "index_tier_counts": counts,
            "top_market": top["market"] if top else None,
            "top_index_tier": top["index_tier"] if top else None,
            "archive_id": archive_receipt.get("archive_id"),
            "receipt_id": archive_receipt.get("receipt_id"),
            "execution_allowed": False,
            "execution_owner": "Q Series",
        }

    def _tier(self, score):
        if score >= 85:
            return "critical"
        if score >= 70:
            return "high"
        if score >= 50:
            return "elevated"
        if score >= 30:
            return "watch"
        return "blocked"

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
            "has_index": bool(self.last_index),
            "index_status": self.last_index.get("index_status"),
            "index_confirmed": self.last_index.get("index_confirmed", False),
            "index_count": self.last_index.get("index_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


qseries_visibility_archive_index_engine = QSeriesVisibilityArchiveIndexEngine()
