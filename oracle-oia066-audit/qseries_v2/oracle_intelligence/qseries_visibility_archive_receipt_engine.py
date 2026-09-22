
"""
OI-134 Q Series Visibility Archive Receipt Engine

Read-only Oracle Intelligence module.
Creates the final archive receipt proving Oracle archived the
visibility packet before handing responsibility to Q Series.
"""

from datetime import datetime, timezone
import hashlib
import json


class QSeriesVisibilityArchiveReceiptEngine:

    module = "oi_134_qseries_visibility_archive_receipt_engine"

    def __init__(self):
        self.last_receipt = {}

    def build_receipt(
        self,
        archive=None,
        integrity=None,
    ):

        archive = archive or {}
        integrity = integrity or {}

        archive_items = archive.get(
            "archive_items",
            []
        )

        receipt_items = []

        for item in archive_items:

            receipt_items.append(
                {
                    "market": item.get("market"),
                    "archive_receipt_score": round(
                        self._float(
                            item.get("archive_score")
                        ),
                        4,
                    ),
                    "archive_receipt_tier": item.get(
                        "archive_tier"
                    ),
                    "archive_rank": item.get(
                        "release_receipt_rank",
                        0,
                    ),
                    "review_conclusion": item.get(
                        "review_conclusion"
                    ),
                    "q_series_visibility": bool(
                        item.get(
                            "q_series_visibility"
                        )
                    ),
                    "execution_permission_from_oracle": False,
                    "execution_owner": "Q Series",
                    "read_only": True,
                }
            )

        receipt_items.sort(
            key=lambda x: (
                x["archive_rank"]
                if x["archive_rank"]
                else 999999,
                -x["archive_receipt_score"],
            )
        )

        receipt_id = self._hash(
            {
                "archive_id": archive.get(
                    "archive_id"
                ),
                "integrity_score": integrity.get(
                    "integrity_score"
                ),
                "items": receipt_items,
            }
        )

        receipt = {

            "module": self.module,

            "status": "ok",

            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),

            "read_only": True,

            "execution_allowed": False,

            "execution_owner": "Q Series",

            "receipt_id": receipt_id,

            "archive_id": archive.get(
                "archive_id"
            ),

            "archive_status": archive.get(
                "archive_status"
            ),

            "archive_confirmed": archive.get(
                "archive_confirmed"
            ),

            "integrity_status": integrity.get(
                "integrity_status"
            ),

            "integrity_score": integrity.get(
                "integrity_score"
            ),

            "receipt_confirmed": (
                archive.get(
                    "archive_confirmed"
                )
                and integrity.get(
                    "archive_integrity_confirmed"
                )
            ),

            "receipt_items": receipt_items,

            "receipt_count": len(
                receipt_items
            ),

            "top_receipt_items": receipt_items[
                :10
            ],

            "receipt_summary": self._summary(
                receipt_items,
                receipt_id,
            ),

            "oracle_boundaries": [

                "Oracle archive receipt is read-only.",

                "Oracle never executes.",

                "Execution ownership belongs to Q Series.",

                "Receipt exists for audit only.",

                "Q Series performs all execution decisions.",

            ],
        }

        self.last_receipt = receipt

        return receipt

    def _summary(
        self,
        items,
        receipt_id,
    ):

        counts = {}

        for item in items:

            tier = item[
                "archive_receipt_tier"
            ]

            counts[tier] = (
                counts.get(
                    tier,
                    0,
                )
                + 1
            )

        top = (
            items[0]
            if items
            else None
        )

        return {

            "headline": (
                f"Archive receipt recorded; "
                f"top market is "
                f"{top['market']}."
                if top
                else "Archive receipt created."
            ),

            "receipt_id": receipt_id,

            "receipt_tier_counts": counts,

            "top_market": (
                top["market"]
                if top
                else None
            ),

            "execution_allowed": False,

            "execution_owner": "Q Series",

        }

    def _hash(
        self,
        payload,
    ):

        return hashlib.sha256(

            json.dumps(
                payload,
                sort_keys=True,
                default=str,
            ).encode()

        ).hexdigest()[:24]

    def _float(
        self,
        value,
        default=0.0,
    ):

        try:
            return float(value)
        except Exception:
            return default

    def diagnostics(self):

        return {

            "module": self.module,

            "status": "ok",

            "receipt_created": bool(
                self.last_receipt
            ),

            "receipt_confirmed": self.last_receipt.get(
                "receipt_confirmed",
                False,
            ),

            "receipt_count": self.last_receipt.get(
                "receipt_count",
                0,
            ),

            "execution_allowed": False,

            "read_only": True,

        }


qseries_visibility_archive_receipt_engine = (
    QSeriesVisibilityArchiveReceiptEngine()
)

