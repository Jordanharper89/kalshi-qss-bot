
"""
ORACLE-063 Final Alert Formatter

Purpose:
- Convert Oracle final decisions into clean Telegram/Q Series-ready alert cards.
- Does NOT send alerts.
- Does NOT place trades.
"""

from datetime import datetime, UTC


class OracleFinalAlertFormatter:
    def __init__(self):
        self.version = "ORACLE-063"

    def format_alert(self, item):
        if not isinstance(item, dict):
            return None

        action = item.get("oracle_final_action", "NO_TRADE")
        score = item.get("oracle_final_score", 0)
        ticker = item.get("ticker", "UNKNOWN")
        title = item.get("title", "Untitled market")

        if action == "READY_FOR_EXECUTION":
            header = "🟢 ORACLE READY"
        elif action == "HUMAN_REVIEW":
            header = "🟡 ORACLE REVIEW"
        elif action == "WATCH":
            header = "🔵 ORACLE WATCH"
        else:
            header = "⚫ ORACLE NO TRADE"

        lines = [
            header,
            f"Ticker: {ticker}",
            f"Market: {title}",
            "",
            f"Final Action: {action}",
            f"Final Score: {score}",
            f"Side: {item.get('side') or item.get('consensus_final_recommendation')}",
            "",
            f"Consensus: {item.get('consensus_final_recommendation')} | {item.get('consensus_confidence')}%",
            f"EV: {item.get('ev_decision')} | {item.get('ev_score')}",
            f"Readiness: {item.get('trade_readiness_verdict')} | {item.get('trade_readiness_score')}",
            f"Gatekeeper: {item.get('execution_decision')}",
            f"Regime: {item.get('market_regime')}",
            "",
            f"Tradability: {item.get('tradability')} | Micro {item.get('microstructure_score')}",
            f"Order Book: {item.get('order_book_rating')} | Fill {item.get('fill_probability')}%",
            f"Flow: {item.get('flow_signal')} | {item.get('flow_score')}",
            f"Portfolio: {item.get('portfolio_decision')} | {item.get('portfolio_exposure_score')}",
        ]

        fd = item.get("final_decision")
        if isinstance(fd, dict):
            blockers = fd.get("blockers") or []
            supports = fd.get("supports") or []
            notes = fd.get("notes") or []

            if blockers:
                lines.append("")
                lines.append("Blockers:")
                for b in blockers[:5]:
                    lines.append(f"- {b}")

            if supports:
                lines.append("")
                lines.append("Supports:")
                for s in supports[:5]:
                    lines.append(f"- {s}")

            if notes:
                lines.append("")
                lines.append("Notes:")
                for n in notes[:5]:
                    lines.append(f"- {n}")

        return {
            "module": "oracle_final_alert_formatter",
            "version": self.version,
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
            "ticker": ticker,
            "final_action": action,
            "final_score": score,
            "alert_card": "\n".join(lines),
            "telegram_ready": action in ("READY_FOR_EXECUTION", "HUMAN_REVIEW", "WATCH"),
            "q_series_ready": action in ("READY_FOR_EXECUTION", "HUMAN_REVIEW"),
        }

    def format_many(self, ranked, limit=10):
        ranked = ranked if isinstance(ranked, list) else []
        alerts = []

        for item in ranked[:limit]:
            alert = self.format_alert(item)
            if alert:
                alerts.append(alert)

        counts = {}
        for a in alerts:
            k = a.get("final_action", "UNKNOWN")
            counts[k] = counts.get(k, 0) + 1

        return {
            "module": "oracle_final_alert_formatter",
            "version": self.version,
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
            "count": len(alerts),
            "action_counts": counts,
            "alerts": alerts,
        }

    def diagnostics(self):
        return {
            "module": "oracle_final_alert_formatter",
            "version": self.version,
            "status": "ok",
            "outputs": ["alert_card", "telegram_ready", "q_series_ready"],
        }


oracle_final_alert_formatter = OracleFinalAlertFormatter()


if __name__ == "__main__":
    sample = [{
        "ticker": "TEST",
        "title": "Sample alert",
        "oracle_final_action": "HUMAN_REVIEW",
        "oracle_final_score": 72,
        "side": "BUY YES",
        "consensus_final_recommendation": "BUY YES",
        "consensus_confidence": 82,
        "ev_decision": "WATCH_EV",
        "ev_score": 8,
        "trade_readiness_verdict": "REVIEW_READY",
        "trade_readiness_score": 70,
        "execution_decision": "REQUIRES_REVIEW",
        "market_regime": "TRENDING_EDGE",
        "tradability": "CAUTION",
        "microstructure_score": 68,
        "order_book_rating": "FAIR",
        "fill_probability": 55,
        "flow_signal": "IMPROVING_FLOW",
        "flow_score": 70,
        "portfolio_decision": "ALLOW",
        "portfolio_exposure_score": 90,
        "final_decision": {
            "blockers": [],
            "supports": ["Positive EV", "Portfolio exposure allows"],
            "notes": ["Gatekeeper requires review"],
        }
    }]

    import pprint
    pprint.pp(oracle_final_alert_formatter.format_many(sample))
