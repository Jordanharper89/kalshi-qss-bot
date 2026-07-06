from services.oracle_watchlist import oracle_watchlist


def oracle_watchlist_text():
    return oracle_watchlist.text()


def oracle_watchlist_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "Refresh Watchlist", "callback_data": "oracle_watchlist"}],
            [{"text": "Back", "callback_data": "oracle_menu"}],
        ]
    }


def oracle_watch_added_text(ticker):
    ticker = str(ticker).upper().strip()
    item = oracle_watchlist.add(ticker)

    return f"""
ORACLE WATCHLIST

Added:
{item.get("ticker")}

Status:
Watching for future Oracle edge changes.
""".strip()