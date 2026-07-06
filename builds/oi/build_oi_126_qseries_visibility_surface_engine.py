from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "qseries_visibility_surface_engine.py"
TEST = ROOT / "test_oi_126_qseries_visibility_surface_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-126 Q Series Visibility Surface Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert validated Oracle transfer dashboard into final Q Series visibility surface.
- Preserve Oracle read-only boundaries and Q Series execution ownership.
- Does not execute trades.
"""

from datetime import datetime, timezone


class QSeriesVisibilitySurfaceEngine:
    module = "oi_126_qseries_visibility_surface_engine"

    def __init__(self):
        self.last_surface = {}

    def build_visibility_surface(self, transfer_dashboard=None, dashboard_validation=None):
        transfer_dashboard = transfer_dashboard or {}
        dashboard_validation = dashboard_validation or {}

        cards = [
            x for x in transfer_dashboard.get("dashboard_cards", [])
            if isinstance(x, dict)
        ]

        dashboard_ready = bool(dashboard_validation.get("dashboard_ready", False))
        validation_status = str(dashboard_validation.get("validation_status") or "unknown")
        dashboard_status = str(transfer_dashboard.get("dashboard_status") or "unknown")

        surface_cards = []
        for card in cards:
            score = self._surface_score(card, dashboard_ready)
            surface_cards.append({
                "market": card.get("market"),
                "surface_score": round(score, 4),
                "surface_tier": self._tier(score),
                "dashboard_rank": int(self._float(card.get("dashboard_rank"), 0)),
                "dashboard_score": round(self._float(card.get("dashboard_score")), 4),
                "dashboard_tier": card.get("dashboard_tier"),
                "receipt_tier": card.get("receipt_tier"),
                "transfer_tier": card.get("transfer_tier"),
                "review_conclusion": card.get("review_conclusion"),
                "q_series_visibility": bool(card.get("q_series_visibility")) and dashboard_ready,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
                "surface_note": self._note(card, score, dashboard_ready),
            })

        surface_cards.sort(
            key=lambda x: (
                -x["surface_score"],
                x["dashboard_rank"] if x["dashboard_rank"] else 999999,
            )
        )

        for idx, card in enumerate(surface_cards, start=1):
            card["surface_rank"] = idx

        surface_status = self._surface_status(dashboard_ready, validation_status, dashboard_status)

        surface = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "input_modules": [
                "oi_124_oracle_transfer_dashboard_engine",
                "oi_125_oracle_transfer_dashboard_validation_engine",
            ],
            "surface_status": surface_status,
            "q_series_visibility_ready": surface_status in {"visible", "visible_with_warnings"},
            "dashboard_status": dashboard_status,
            "validation_status": validation_status,
            "validation_score": round(self._float(dashboard_validation.get("validation_score")), 4),
            "surface_count": len(surface_cards),
            "surface_cards": surface_cards,
            "top_surface_cards": surface_cards[:10],
            "blocked_surface_cards": [x for x in surface_cards if not x["q_series_visibility"]],
            "surface_summary": self._summary(surface_cards, surface_status, transfer_dashboard, dashboard_validation),
            "oracle_surface_boundaries": [
                "Oracle visibility surface is read-only.",
                "Oracle visibility surface grants no execution permission.",
                "Oracle does not execute.",
                "Oracle does not approve execution.",
                "Q Series owns execution evaluation and execution decisions.",
            ],
        }

        self.last_surface = surface
        return surface

    def _surface_score(self, card, dashboard_ready):
        base = self._float(card.get("dashboard_score"))
        ready_bonus = 5 if dashboard_ready else -30
        visibility_bonus = 5 if card.get("q_series_visibility") is True else -25
        tier_bonus = {
            "critical": 5,
            "high": 3,
            "elevated": 1,
            "watch": 0,
            "blocked": -10,
        }.get(str(card.get("dashboard_tier") or ""), 0)

        return max(0.0, min(100.0, base + ready_bonus + visibility_bonus + tier_bonus))

    def _surface_status(self, dashboard_ready, validation_status, dashboard_status):
        if dashboard_ready and validation_status == "validated" and dashboard_status == "confirmed_visible":
            return "visible"
        if dashboard_ready and validation_status == "validated_with_warnings":
            return "visible_with_warnings"
        if validation_status in {"needs_review", "invalid"}:
            return "blocked_by_validation"
        return "blocked"

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

    def _note(self, card, score, dashboard_ready):
        market = card.get("market")
        if not dashboard_ready:
            return f"{market} visibility blocked because dashboard validation is not ready."
        return (
            f"{market} Q Series visibility tier is {self._tier(score)}. "
            "Oracle provides read-only visibility only; Q Series owns execution."
        )

    def _summary(self, cards, status, dashboard, validation):
        counts = {}
        for card in cards:
            tier = card["surface_tier"]
            counts[tier] = counts.get(tier, 0) + 1

        top = cards[0] if cards else None

        if status == "visible" and top:
            headline = f"Q Series visibility surface is live; top visible market is {top['market']}."
        elif status == "visible":
            headline = "Q Series visibility surface is live with no market cards."
        else:
            headline = f"Q Series visibility surface is {status}; review required."

        return {
            "headline": headline,
            "surface_status": status,
            "surface_tier_counts": counts,
            "top_market": top["market"] if top else None,
            "top_surface_tier": top["surface_tier"] if top else None,
            "dashboard_status": dashboard.get("dashboard_status"),
            "validation_status": validation.get("validation_status"),
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
            "has_surface": bool(self.last_surface),
            "surface_status": self.last_surface.get("surface_status"),
            "surface_count": self.last_surface.get("surface_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


qseries_visibility_surface_engine = QSeriesVisibilitySurfaceEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.qseries_visibility_surface_engine import qseries_visibility_surface_engine


def test_oi_126_qseries_visibility_surface_engine():
    dashboard = {
        "status": "ok",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "dashboard_status": "confirmed_visible",
        "receipt_confirmed": True,
        "ledger_integrity_confirmed": True,
        "transfer_ready": True,
        "dashboard_cards": [
            {
                "market": "CRYPTO",
                "dashboard_rank": 1,
                "dashboard_score": 100.0,
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
                "dashboard_rank": 2,
                "dashboard_score": 92.0,
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

    validation = {
        "validation_status": "validated",
        "validation_score": 100.0,
        "dashboard_ready": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "read_only": True,
    }

    surface = qseries_visibility_surface_engine.build_visibility_surface(dashboard, validation)

    assert surface["status"] == "ok"
    assert surface["read_only"] is True
    assert surface["execution_allowed"] is False
    assert surface["execution_owner"] == "Q Series"
    assert surface["surface_status"] == "visible"
    assert surface["q_series_visibility_ready"] is True
    assert surface["surface_count"] == 2
    assert surface["surface_cards"][0]["surface_rank"] == 1
    assert surface["surface_cards"][0]["market"] == "CRYPTO"
    assert surface["surface_summary"]["execution_allowed"] is False

    diag = qseries_visibility_surface_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["surface_status"] == "visible"

    print("[PASS] OI-126 Q Series Visibility Surface Engine")
    print({
        "surface_status": surface["surface_status"],
        "surface_count": surface["surface_count"],
        "summary": surface["surface_summary"],
        "top": surface["surface_cards"][0],
    })


if __name__ == "__main__":
    test_oi_126_qseries_visibility_surface_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .qseries_visibility_surface_engine import qseries_visibility_surface_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-126 INSTALLER")
print(" Q Series Visibility Surface Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-126 installed")
print()
print("Run:")
print("py test_oi_126_qseries_visibility_surface_engine.py")