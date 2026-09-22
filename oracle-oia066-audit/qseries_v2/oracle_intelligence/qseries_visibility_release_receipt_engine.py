
"""
OI-131 Q Series Visibility Release Receipt Engine
Read-only Oracle Intelligence module.

Purpose:
- Create the final receipt after Q Series visibility release ledger integrity is verified.
- Confirm visibility release, ledger verification, read-only boundaries, and Q Series ownership.
- Does not execute trades.
- Oracle remains strictly read-only.
"""

from datetime import datetime, timezone


class QSeriesVisibilityReleaseReceiptEngine:
    module = "oi_131_qseries_visibility_release_receipt_engine"

    def __init__(self):
        self.last_receipt = {}

    def build_release_receipt(self, release_ledger=None, ledger_integrity=None):
        release_ledger = release_ledger or {}
        ledger_integrity = ledger_integrity or {}

        ledger_items = [
            x for x in release_ledger.get("release_ledger_items", [])
            if isinstance(x, dict)
        ]

        integrity_confirmed = bool(ledger_integrity.get("release_ledger_integrity_confirmed", False))
        integrity_status = str(ledger_integrity.get("integrity_status") or "unknown")
        release_confirmed = bool(release_ledger.get("release_confirmed", False))
        release_status = str(release_ledger.get("release_status") or "unknown")

        receipt_items = []
        for item in ledger_items:
            score = self._receipt_score(item, integrity_confirmed, release_confirmed)

            receipt_items.append({
                "market": item.get("market"),
                "receipt_score": round(score, 4),
                "receipt_tier": self._tier(score),
                "release_rank": int(self._float(item.get("release_rank"), 0)),
                "release_score": round(self._float(item.get("release_score")), 4),
                "release_tier": item.get("release_tier"),
                "surface_tier": item.get("surface_tier"),
                "dashboard_tier": item.get("dashboard_tier"),
                "receipt_source_tier": item.get("receipt_tier"),
                "transfer_tier": item.get("transfer_tier"),
                "review_conclusion": item.get("review_conclusion"),
                "q_series_visibility": bool(item.get("q_series_visibility")),
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
                "receipt_note": self._note(item, score, integrity_confirmed, release_confirmed),
            })

        receipt_items.sort(
            key=lambda x: (
                -x["receipt_score"],
                x["release_rank"] if x["release_rank"] else 999999,
            )
        )

        for idx, item in enumerate(receipt_items, start=1):
            item["release_receipt_rank"] = idx

        receipt_status = self._receipt_status(
            integrity_confirmed=integrity_confirmed,
            integrity_status=integrity_status,
            release_confirmed=release_confirmed,
            release_status=release_status,
        )

        receipt = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "input_modules": [
                "oi_129_qseries_visibility_release_ledger_engine",
                "oi_130_qseries_visibility_release_ledger_integrity_engine",
            ],
            "release_receipt_status": receipt_status,
            "release_receipt_confirmed": receipt_status == "confirmed",
            "release_ledger_id": release_ledger.get("release_ledger_id") or ledger_integrity.get("release_ledger_id"),
            "release_ledger_status": release_ledger.get("release_ledger_status"),
            "release_status": release_status,
            "release_confirmed": release_confirmed,
            "integrity_status": integrity_status,
            "integrity_score": round(self._float(ledger_integrity.get("integrity_score")), 4),
            "release_ledger_integrity_confirmed": integrity_confirmed,
            "receipt_count": len(receipt_items),
            "release_receipt_items": receipt_items,
            "top_release_receipt_items": receipt_items[:10],
            "release_receipt_summary": self._summary(
                receipt_status=receipt_status,
                release_ledger=release_ledger,
                ledger_integrity=ledger_integrity,
                items=receipt_items,
            ),
            "oracle_release_receipt_boundaries": [
                "Q Series visibility release receipt is read-only.",
                "Oracle grants no execution permission.",
                "Oracle does not execute.",
                "Oracle does not approve execution.",
                "Q Series owns execution evaluation and decisions.",
            ],
        }

        self.last_receipt = receipt
        return receipt

    def _receipt_score(self, item, integrity_confirmed, release_confirmed):
        base = self._float(item.get("release_score"))
        integrity_bonus = 6 if integrity_confirmed else -30
        release_bonus = 6 if release_confirmed else -30
        visibility_bonus = 4 if item.get("q_series_visibility") is True else -20
        tier_bonus = {
            "critical": 5,
            "high": 3,
            "elevated": 1,
            "watch": 0,
            "blocked": -10,
        }.get(str(item.get("release_tier") or ""), 0)

        return max(0.0, min(100.0, base + integrity_bonus + release_bonus + visibility_bonus + tier_bonus))

    def _receipt_status(self, integrity_confirmed, integrity_status, release_confirmed, release_status):
        if integrity_confirmed and integrity_status == "verified" and release_confirmed and release_status == "released":
            return "confirmed"
        if integrity_status == "verified_with_warnings":
            return "confirmed_with_warnings"
        if integrity_status in {"needs_review", "failed"}:
            return "blocked_by_integrity"
        if not release_confirmed:
            return "blocked_by_release"
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

    def _note(self, item, score, integrity_confirmed, release_confirmed):
        market = item.get("market")
        if not integrity_confirmed:
            return f"{market} release receipt blocked because ledger integrity is not confirmed."
        if not release_confirmed:
            return f"{market} release receipt blocked because visibility release is not confirmed."
        return (
            f"{market} release receipt tier is {self._tier(score)}. "
            "Oracle confirms read-only visibility release receipt; Q Series owns execution."
        )

    def _summary(self, receipt_status, release_ledger, ledger_integrity, items):
        counts = {}
        for item in items:
            tier = item["receipt_tier"]
            counts[tier] = counts.get(tier, 0) + 1

        top = items[0] if items else None

        if receipt_status == "confirmed" and top:
            headline = f"Q Series visibility release receipt confirmed; top market is {top['market']}."
        elif receipt_status == "confirmed":
            headline = "Q Series visibility release receipt confirmed with no market items."
        else:
            headline = f"Q Series visibility release receipt status is {receipt_status}; review required."

        return {
            "headline": headline,
            "release_receipt_status": receipt_status,
            "receipt_tier_counts": counts,
            "top_market": top["market"] if top else None,
            "top_receipt_tier": top["receipt_tier"] if top else None,
            "release_ledger_id": release_ledger.get("release_ledger_id") or ledger_integrity.get("release_ledger_id"),
            "integrity_score": ledger_integrity.get("integrity_score"),
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
            "has_receipt": bool(self.last_receipt),
            "release_receipt_status": self.last_receipt.get("release_receipt_status"),
            "release_receipt_confirmed": self.last_receipt.get("release_receipt_confirmed", False),
            "receipt_count": self.last_receipt.get("receipt_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


qseries_visibility_release_receipt_engine = QSeriesVisibilityReleaseReceiptEngine()
