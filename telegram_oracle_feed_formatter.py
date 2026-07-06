"""
Telegram Oracle Feed Formatter

Purpose:
- Format Oracle Opportunity Feed for Telegram.
- Mobile-readable.
- No trading execution.
"""

from typing import Any, Dict, List


def format_oracle_feed_message(opportunities: List[Dict[str, Any]]) -> str:
    if not opportunities:
        return (
            "🔮 <b>Oracle Opportunity Feed</b>\n\n"
            "No qualifying live opportunities right now.\n\n"
            "Oracle is still watching for edge changes."
        )

    lines = [
        "🔮 <b>Oracle Opportunity Feed</b>",
        "",
        f"Top {len(opportunities)} live edges",
        "",
    ]

    for opp in opportunities:
        rank = opp.get("rank", "?")
        ticker = opp.get("ticker", "UNKNOWN")
        title = opp.get("title") or "Untitled market"
        action = opp.get("action", "PASS")
        grade = opp.get("grade", "N/A")
        confidence = _fmt_num(opp.get("confidence_score"))
        edge = _fmt_num(opp.get("edge"))
        fair_value = _fmt_num(opp.get("oracle_fair_value"))
        yes_price = _fmt_num(opp.get("yes_price"))
        no_price = _fmt_num(opp.get("no_price"))
        score = _fmt_num(opp.get("opportunity_score"))

        icon = "🟢" if action == "BUY YES" else "🔴" if action == "BUY NO" else "⚪"

        lines.extend(
            [
                f"{icon} <b>#{rank} {action}</b>",
                f"<b>{ticker}</b>",
                _shorten(title, 80),
                f"Grade: <b>{grade}</b> | Score: <b>{score}</b>",
                f"Confidence: <b>{confidence}%</b>",
                f"Edge: <b>{edge}c</b>",
                f"Fair Value: <b>{fair_value}c</b>",
                f"YES: {yes_price}c | NO: {no_price}c",
                "────────────",
            ]
        )

    lines.append("Q Series handles execution only after confirmation.")

    return "\n".join(lines)


def _fmt_num(value: Any) -> str:
    try:
        return f"{float(value):.1f}"
    except Exception:
        return "0.0"


def _shorten(text: str, max_len: int) -> str:
    text = str(text).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."