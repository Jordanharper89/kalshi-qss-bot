from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "qseries_visibility_archive_engine.py"
TEST = ROOT / "test_oi_132_qseries_visibility_archive_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
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
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.qseries_visibility_archive_engine import qseries_visibility_archive_engine


def test_oi_132_qseries_visibility_archive_engine():
    receipt = {
        "release_receipt_status": "confirmed",
        "release_receipt_confirmed": True,
        "release_ledger_id": "abc123def456ghi789jkl012",
        "integrity_status": "verified",
        "integrity_score": 100.0,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
        "release_receipt_items": [
            {
                "market": "CRYPTO",
                "release_receipt_rank": 1,
                "receipt_score": 100.0,
                "receipt_tier": "critical",
                "release_score": 100.0,
                "release_tier": "critical",
                "surface_tier": "critical",
                "dashboard_tier": "critical",
                "transfer_tier": "critical",
                "review_conclusion": "high_confidence_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
            {
                "market": "NASDAQ",
                "release_receipt_rank": 2,
                "receipt_score": 100.0,
                "receipt_tier": "critical",
                "release_score": 100.0,
                "release_tier": "critical",
                "surface_tier": "critical",
                "dashboard_tier": "critical",
                "transfer_tier": "critical",
                "review_conclusion": "confirmed_review",
                "q_series_visibility": True,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
        ],
    }

    archive = qseries_visibility_archive_engine.build_archive(receipt)

    assert archive["status"] == "ok"
    assert archive["read_only"] is True
    assert archive["execution_allowed"] is False
    assert archive["execution_owner"] == "Q Series"
    assert archive["archive_status"] == "archived"
    assert archive["archive_confirmed"] is True
    assert len(archive["archive_id"]) == 24
    assert archive["archive_count"] == 2
    assert archive["archive_items"][0]["market"] == "CRYPTO"
    assert archive["archive_summary"]["execution_allowed"] is False

    diag = qseries_visibility_archive_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["archive_confirmed"] is True

    print("[PASS] OI-132 Q Series Visibility Archive Engine")
    print({
        "archive_status": archive["archive_status"],
        "archive_id": archive["archive_id"],
        "summary": archive["archive_summary"],
        "top": archive["archive_items"][0],
    })


if __name__ == "__main__":
    test_oi_132_qseries_visibility_archive_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .qseries_visibility_archive_engine import qseries_visibility_archive_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-132 INSTALLER")
print(" Q Series Visibility Archive Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-132 installed")
print()
print("Run:")
print("py test_oi_132_qseries_visibility_archive_engine.py")