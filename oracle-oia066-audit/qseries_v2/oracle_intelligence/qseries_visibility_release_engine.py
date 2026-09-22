
"""
OI-128 Q Series Visibility Release Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert validated Q Series visibility surface into a final release record.
- Confirm Oracle visibility is safe, read-only, and execution remains owned by Q Series.
- Does not execute trades.
- Oracle remains strictly read-only.
"""

from datetime import datetime, timezone


class QSeriesVisibilityReleaseEngine:
    module = "oi_128_qseries_visibility_release_engine"

    def __init__(self):
        self.last_release = {}

    def build_release(self, visibility_surface=None, surface_validation=None):
        visibility_surface = visibility_surface or {}
        surface_validation = surface_validation or {}

        cards = [
            x for x in visibility_surface.get("surface_cards", [])
            if isinstance(x, dict)
        ]

        validation_status = str(surface_validation.get("validation_status") or "unknown")
        surface_status = str(visibility_surface.get("surface_status") or "unknown")
        surface_ready = bool(surface_validation.get("surface_ready_for_qseries", False))
        qseries_ready = bool(visibility_surface.get("q_series_visibility_ready", False))

        release_items = []
        for card in cards:
            release_score = self._release_score(card, surface_ready, qseries_ready)

            release_items.append({
                "market": card.get("market"),
                "release_score": round(release_score, 4),
                "release_tier": self._tier(release_score),
                "surface_rank": int(self._float(card.get("surface_rank"), 0)),
                "surface_score": round(self._float(card.get("surface_score")), 4),
                "surface_tier": card.get("surface_tier"),
                "dashboard_tier": card.get("dashboard_tier"),
                "receipt_tier": card.get("receipt_tier"),
                "transfer_tier": card.get("transfer_tier"),
                "review_conclusion": card.get("review_conclusion"),
                "q_series_visibility": bool(card.get("q_series_visibility")) and surface_ready and qseries_ready,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
                "release_note": self._note(card, release_score, surface_ready, qseries_ready),
            })

        release_items.sort(
            key=lambda x: (
                -x["release_score"],
                x["surface_rank"] if x["surface_rank"] else 999999,
            )
        )

        for idx, item in enumerate(release_items, start=1):
            item["release_rank"] = idx

        release_status = self._release_status(surface_ready, qseries_ready, validation_status, surface_status)

        release = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "input_modules": [
                "oi_126_qseries_visibility_surface_engine",
                "oi_127_qseries_visibility_surface_validation_engine",
            ],
            "release_status": release_status,
            "release_confirmed": release_status == "released",
            "surface_status": surface_status,
            "validation_status": validation_status,
            "validation_score": round(self._float(surface_validation.get("validation_score")), 4),
            "surface_ready_for_qseries": surface_ready,
            "q_series_visibility_ready": qseries_ready,
            "release_count": len(release_items),
            "release_items": release_items,
            "top_release_items": release_items[:10],
            "blocked_release_items": [x for x in release_items if not x["q_series_visibility"]],
            "release_summary": self._summary(release_items, release_status, visibility_surface, surface_validation),
            "oracle_release_boundaries": [
                "Oracle visibility release is read-only.",
                "Oracle release grants no execution permission.",
                "Oracle does not execute.",
                "Oracle does not approve execution.",
                "Q Series owns execution evaluation and execution decisions.",
            ],
        }

        self.last_release = release
        return release

    def _release_score(self, card, surface_ready, qseries_ready):
        base = self._float(card.get("surface_score"))
        ready_bonus = 5 if surface_ready else -35
        visibility_bonus = 5 if qseries_ready and card.get("q_series_visibility") else -25
        tier_bonus = {
            "critical": 5,
            "high": 3,
            "elevated": 1,
            "watch": 0,
            "blocked": -10,
        }.get(str(card.get("surface_tier") or ""), 0)

        return max(0.0, min(100.0, base + ready_bonus + visibility_bonus + tier_bonus))

    def _release_status(self, surface_ready, qseries_ready, validation_status, surface_status):
        if surface_ready and qseries_ready and validation_status == "validated" and surface_status == "visible":
            return "released"
        if surface_ready and qseries_ready and validation_status == "validated_with_warnings":
            return "released_with_warnings"
        if not surface_ready:
            return "blocked_by_validation"
        if not qseries_ready:
            return "blocked_by_visibility"
        return "review_required"

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

    def _note(self, card, score, surface_ready, qseries_ready):
        market = card.get("market")
        if not surface_ready:
            return f"{market} release blocked because surface validation is not ready."
        if not qseries_ready:
            return f"{market} release blocked because Q Series visibility is not ready."
        return (
            f"{market} release tier is {self._tier(score)}. "
            "Oracle releases read-only visibility only; Q Series owns all execution decisions."
        )

    def _summary(self, release_items, release_status, visibility_surface, surface_validation):
        counts = {}
        for item in release_items:
            tier = item["release_tier"]
            counts[tier] = counts.get(tier, 0) + 1

        top = release_items[0] if release_items else None

        if release_status == "released" and top:
            headline = f"Q Series visibility release confirmed; top released market is {top['market']}."
        elif release_status == "released":
            headline = "Q Series visibility release confirmed with no market items."
        else:
            headline = f"Q Series visibility release is {release_status}; review required."

        return {
            "headline": headline,
            "release_status": release_status,
            "release_tier_counts": counts,
            "top_market": top["market"] if top else None,
            "top_release_tier": top["release_tier"] if top else None,
            "surface_status": visibility_surface.get("surface_status"),
            "validation_status": surface_validation.get("validation_status"),
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
            "has_release": bool(self.last_release),
            "release_status": self.last_release.get("release_status"),
            "release_confirmed": self.last_release.get("release_confirmed", False),
            "release_count": self.last_release.get("release_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


qseries_visibility_release_engine = QSeriesVisibilityReleaseEngine()
