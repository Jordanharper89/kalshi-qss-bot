
"""
OI-124 Oracle Transfer Dashboard Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert confirmed Oracle transfer receipts into a dashboard-ready transfer view.
- Summarize receipt status, transfer readiness, top markets, tiers, and Q Series ownership.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from datetime import datetime, timezone


class OracleTransferDashboardEngine:
    module = "oi_124_oracle_transfer_dashboard_engine"

    def __init__(self):
        self.last_dashboard = {}

    def build_dashboard(self, transfer_receipt=None):
        transfer_receipt = transfer_receipt or {}

        receipt_items = [
            x for x in transfer_receipt.get("receipt_items", [])
            if isinstance(x, dict)
        ]

        cards = []
        for item in receipt_items:
            score = self._float(item.get("receipt_score"))
            cards.append({
                "market": item.get("market"),
                "dashboard_score": round(score, 4),
                "dashboard_tier": self._tier(score),
                "receipt_rank": int(self._float(item.get("receipt_rank"), 0)),
                "receipt_tier": item.get("receipt_tier"),
                "transfer_tier": item.get("transfer_tier"),
                "intake_tier": item.get("intake_tier"),
                "handoff_tier": item.get("handoff_tier"),
                "review_conclusion": item.get("review_conclusion"),
                "q_series_visibility": bool(item.get("q_series_visibility")),
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
                "dashboard_note": self._note(item, score),
            })

        cards.sort(
            key=lambda x: (
                -x["dashboard_score"],
                x["receipt_rank"] if x["receipt_rank"] else 999999,
            )
        )

        for idx, card in enumerate(cards, start=1):
            card["dashboard_rank"] = idx

        dashboard_status = self._dashboard_status(transfer_receipt)

        dashboard = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "input_module": "oi_123_oracle_transfer_receipt_engine",
            "dashboard_status": dashboard_status,
            "receipt_status": transfer_receipt.get("receipt_status"),
            "receipt_confirmed": bool(transfer_receipt.get("receipt_confirmed", False)),
            "ledger_integrity_confirmed": bool(transfer_receipt.get("ledger_integrity_confirmed", False)),
            "transfer_ready": bool(transfer_receipt.get("transfer_ready", False)),
            "transfer_status": transfer_receipt.get("transfer_status"),
            "ledger_entry_id": transfer_receipt.get("ledger_entry_id"),
            "card_count": len(cards),
            "dashboard_cards": cards,
            "top_dashboard_cards": cards[:10],
            "critical_cards": [x for x in cards if x["dashboard_tier"] == "critical"],
            "dashboard_summary": self._summary(transfer_receipt, cards, dashboard_status),
            "oracle_dashboard_boundaries": [
                "Oracle transfer dashboard is read-only.",
                "Dashboard cards are visibility artifacts only.",
                "Oracle does not execute.",
                "Oracle does not approve execution.",
                "Q Series owns execution evaluation and decisions.",
            ],
        }

        self.last_dashboard = dashboard
        return dashboard

    def _dashboard_status(self, receipt):
        if (
            receipt.get("receipt_status") == "confirmed"
            and receipt.get("receipt_confirmed") is True
            and receipt.get("ledger_integrity_confirmed") is True
            and receipt.get("transfer_ready") is True
        ):
            return "confirmed_visible"
        if receipt.get("receipt_status") == "confirmed_with_warnings":
            return "visible_with_warnings"
        if str(receipt.get("receipt_status") or "").startswith("blocked"):
            return "blocked"
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

    def _note(self, item, score):
        market = item.get("market")
        return (
            f"{market} dashboard tier is {self._tier(score)}. "
            "Oracle confirms read-only visibility only; Q Series owns execution decisions."
        )

    def _summary(self, receipt, cards, dashboard_status):
        counts = {}
        for card in cards:
            tier = card["dashboard_tier"]
            counts[tier] = counts.get(tier, 0) + 1

        top = cards[0] if cards else None

        if dashboard_status == "confirmed_visible" and top:
            headline = f"Oracle transfer dashboard confirmed visible; top market is {top['market']}."
        elif dashboard_status == "confirmed_visible":
            headline = "Oracle transfer dashboard confirmed visible with no market cards."
        else:
            headline = f"Oracle transfer dashboard status is {dashboard_status}; review required."

        return {
            "headline": headline,
            "dashboard_status": dashboard_status,
            "dashboard_tier_counts": counts,
            "top_market": top["market"] if top else None,
            "top_dashboard_tier": top["dashboard_tier"] if top else None,
            "receipt_status": receipt.get("receipt_status"),
            "ledger_entry_id": receipt.get("ledger_entry_id"),
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
            "has_dashboard": bool(self.last_dashboard),
            "dashboard_status": self.last_dashboard.get("dashboard_status"),
            "card_count": self.last_dashboard.get("card_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_transfer_dashboard_engine = OracleTransferDashboardEngine()
