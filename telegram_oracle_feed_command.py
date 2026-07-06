"""
Telegram Oracle Feed Command

Purpose:
- Wires /oracle_feed into Telegram.
- Pulls watched markets.
- Builds Oracle Opportunity Feed.
- Formats mobile-readable Telegram message.
"""

from typing import Any, Dict, List

from oracle_opportunity_feed import build_oracle_opportunity_feed
from telegram_oracle_feed_formatter import format_oracle_feed_message


def handle_oracle_feed_command(
    bot: Any,
    chat_id: int,
    watchlist_service: Any,
    min_grade: str = "B+",
    min_edge: float = 2.0,
    min_confidence: float = 60.0,
    max_items: int = 10,
) -> Dict[str, Any]:
    watched_markets = _load_watched_markets(watchlist_service)

    opportunities = build_oracle_opportunity_feed(
        watched_markets=watched_markets,
        min_grade=min_grade,
        min_edge=min_edge,
        min_confidence=min_confidence,
        max_items=max_items,
    )

    message = format_oracle_feed_message(opportunities)

    bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    return {
        "status": "OK",
        "command": "/oracle_feed",
        "watched_markets": len(watched_markets),
        "opportunities": len(opportunities),
    }


def _load_watched_markets(watchlist_service: Any) -> List[Dict[str, Any]]:
    if hasattr(watchlist_service, "list_watched_markets"):
        return watchlist_service.list_watched_markets() or []

    if hasattr(watchlist_service, "get_all"):
        return watchlist_service.get_all() or []

    if hasattr(watchlist_service, "list_all"):
        return watchlist_service.list_all() or []

    raise AttributeError(
        "Watchlist service must provide list_watched_markets(), get_all(), or list_all()."
    )