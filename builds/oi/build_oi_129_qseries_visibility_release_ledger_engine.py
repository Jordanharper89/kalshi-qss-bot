from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "qseries_visibility_release_ledger_engine.py"
TEST = ROOT / "test_oi_129_qseries_visibility_release_ledger_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-129 Q Series Visibility Release Ledger Engine
Read-only Oracle Intelligence module.

Purpose:
- Record the confirmed Q Series visibility release from OI-128.
- Create deterministic read-only ledger entries for release traceability.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from datetime import datetime, timezone
import hashlib
import json


class QSeriesVisibilityReleaseLedgerEngine:
    module = "oi_129_qseries_visibility_release_ledger_engine"

    def __init__(self):
        self.last_ledger = {}

    def build_release_ledger(self, visibility_release=None):
        visibility_release = visibility_release or {}

        release_items = [
            x for x in visibility_release.get("release_items", [])
            if isinstance(x, dict)
        ]

        ledger_items = []
        for item in release_items:
            ledger_items.append({
                "market": item.get("market"),
                "release_rank": int(self._float(item.get("release_rank"), 0)),
                "release_score": round(self._float(item.get("release_score")), 4),
                "release_tier": item.get("release_tier"),
                "surface_tier": item.get("surface_tier"),
                "dashboard_tier": item.get("dashboard_tier"),
                "receipt_tier": item.get("receipt_tier"),
                "transfer_tier": item.get("transfer_tier"),
                "review_conclusion": item.get("review_conclusion"),
                "q_series_visibility": bool(item.get("q_series_visibility")),
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
            })

        ledger_items.sort(
            key=lambda x: (
                x["release_rank"] if x["release_rank"] else 999999,
                -x["release_score"],
            )
        )

        ledger_hash = self._hash_record({
            "release_status": visibility_release.get("release_status"),
            "release_confirmed": visibility_release.get("release_confirmed"),
            "surface_status": visibility_release.get("surface_status"),
            "validation_status": visibility_release.get("validation_status"),
            "items": ledger_items,
        })

        ledger = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "input_module": "oi_128_qseries_visibility_release_engine",
            "release_ledger_id": ledger_hash,
            "release_ledger_status": self._ledger_status(visibility_release),
            "release_status": visibility_release.get("release_status"),
            "release_confirmed": bool(visibility_release.get("release_confirmed", False)),
            "surface_status": visibility_release.get("surface_status"),
            "validation_status": visibility_release.get("validation_status"),
            "validation_score": round(self._float(visibility_release.get("validation_score")), 4),
            "release_count": len(ledger_items),
            "release_ledger_items": ledger_items,
            "top_release_ledger_items": ledger_items[:10],
            "release_ledger_summary": self._summary(visibility_release, ledger_items, ledger_hash),
            "immutability_note": "Release ledger id is deterministic from release content and read-only metadata.",
            "oracle_release_ledger_boundaries": [
                "Oracle release ledger is read-only.",
                "Oracle release ledger grants no execution permission.",
                "Oracle does not execute.",
                "Oracle does not approve execution.",
                "Q Series owns execution evaluation and decisions.",
            ],
        }

        self.last_ledger = ledger
        return ledger

    def _ledger_status(self, release):
        if release.get("release_confirmed") is True and release.get("release_status") == "released":
            return "recorded_released_visibility"
        if release.get("release_status") == "released_with_warnings":
            return "recorded_warning_visibility"
        return "recorded_blocked_visibility"

    def _summary(self, release, items, ledger_hash):
        counts = {}
        for item in items:
            tier = item["release_tier"]
            counts[tier] = counts.get(tier, 0) + 1

        top = items[0] if items else None

        return {
            "release_ledger_id": ledger_hash,
            "headline": (
                f"Q Series visibility release ledger recorded; top market is {top['market']}."
                if top else
                "Q Series visibility release ledger recorded with no market items."
            ),
            "release_tier_counts": counts,
            "top_market": top["market"] if top else None,
            "top_release_tier": top["release_tier"] if top else None,
            "release_status": release.get("release_status"),
            "release_confirmed": bool(release.get("release_confirmed", False)),
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
            "has_ledger": bool(self.last_ledger),
            "release_ledger_status": self.last_ledger.get("release_ledger_status"),
            "release_count": self.last_ledger.get("release_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


qseries_visibility_release_ledger_engine = QSeriesVisibilityReleaseLedgerEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.qseries_visibility_release_ledger_engine import qseries_visibility_release_ledger_engine


def test_oi_129_qseries_visibility_release_ledger_engine():
    release = {
        "release_status": "released",
        "release_confirmed": True,
        "surface_status": "visible",
        "validation_status": "validated",
        "validation_score": 100.0,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
        "release_items": [
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
        ],
    }

    ledger = qseries_visibility_release_ledger_engine.build_release_ledger(release)

    assert ledger["status"] == "ok"
    assert ledger["read_only"] is True
    assert ledger["execution_allowed"] is False
    assert ledger["execution_owner"] == "Q Series"
    assert ledger["release_ledger_status"] == "recorded_released_visibility"
    assert ledger["release_confirmed"] is True
    assert ledger["release_count"] == 2
    assert len(ledger["release_ledger_id"]) == 24
    assert ledger["release_ledger_items"][0]["market"] == "CRYPTO"
    assert ledger["release_ledger_summary"]["execution_allowed"] is False

    diag = qseries_visibility_release_ledger_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False

    print("[PASS] OI-129 Q Series Visibility Release Ledger Engine")
    print({
        "release_ledger_status": ledger["release_ledger_status"],
        "release_ledger_id": ledger["release_ledger_id"],
        "summary": ledger["release_ledger_summary"],
        "top": ledger["release_ledger_items"][0],
    })


if __name__ == "__main__":
    test_oi_129_qseries_visibility_release_ledger_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .qseries_visibility_release_ledger_engine import qseries_visibility_release_ledger_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-129 INSTALLER")
print(" Q Series Visibility Release Ledger Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-129 installed")
print()
print("Run:")
print("py test_oi_129_qseries_visibility_release_ledger_engine.py")