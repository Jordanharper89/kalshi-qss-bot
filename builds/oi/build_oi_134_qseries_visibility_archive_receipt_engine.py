from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "qseries_visibility_archive_receipt_engine.py"
TEST = ROOT / "test_oi_134_qseries_visibility_archive_receipt_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
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

''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.qseries_visibility_archive_receipt_engine import (
    qseries_visibility_archive_receipt_engine,
)


def test_oi_134_qseries_visibility_archive_receipt_engine():

    archive = {
        "archive_id": "archive-001",
        "archive_status": "archived",
        "archive_confirmed": True,
        "archive_items": [
            {
                "market": "CRYPTO",
                "archive_score": 100.0,
                "archive_tier": "critical",
                "release_receipt_rank": 1,
                "review_conclusion": "high_confidence_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
            {
                "market": "NASDAQ",
                "archive_score": 95.4,
                "archive_tier": "high",
                "release_receipt_rank": 2,
                "review_conclusion": "confirmed_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
        ],
    }

    integrity = {
        "integrity_status": "verified",
        "integrity_score": 100.0,
        "archive_integrity_confirmed": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
    }

    receipt = qseries_visibility_archive_receipt_engine.build_receipt(
        archive,
        integrity,
    )

    assert receipt["status"] == "ok"
    assert receipt["read_only"] is True
    assert receipt["execution_allowed"] is False
    assert receipt["execution_owner"] == "Q Series"
    assert receipt["receipt_confirmed"] is True
    assert receipt["receipt_count"] == 2
    assert receipt["receipt_items"][0]["market"] == "CRYPTO"

    diag = qseries_visibility_archive_receipt_engine.diagnostics()

    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["receipt_confirmed"] is True

    print("[PASS] OI-134 Q Series Visibility Archive Receipt Engine")
    print(
        {
            "receipt_id": receipt["receipt_id"],
            "receipt_confirmed": receipt["receipt_confirmed"],
            "summary": receipt["receipt_summary"],
            "top": receipt["receipt_items"][0],
        }
    )


if __name__ == "__main__":
    test_oi_134_qseries_visibility_archive_receipt_engine()

''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(
        encoding="utf-8"
    )
else:
    init_text = ""

line = (
    "from .qseries_visibility_archive_receipt_engine "
    "import qseries_visibility_archive_receipt_engine\n"
)

if line not in init_text:
    INIT.write_text(
        init_text.rstrip() + "\n" + line,
        encoding="utf-8",
    )

print("========================================")
print(" OI-134 INSTALLER")
print(" Q Series Visibility Archive Receipt Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-134 installed")
print()
print("Run:")
print("py test_oi_134_qseries_visibility_archive_receipt_engine.py")