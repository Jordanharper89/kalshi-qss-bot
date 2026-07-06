from services.trade_journal import trade_journal


def journal_text(limit=15):
    events = trade_journal.recent(limit=limit)

    if not events:
        return """
TRADE JOURNAL

No journal events found yet.
""".strip()

    lines = ["TRADE JOURNAL", ""]

    for event in reversed(events):
        timestamp = event.get("timestamp") or event.get("time")
        event_type = event.get("event") or event.get("event_type")
        ticker = event.get("ticker") or "N/A"

        lines.append(f"{event_type}")
        lines.append(f"Ticker: {ticker}")
        lines.append(f"Time: {timestamp}")
        lines.append("")

    return "\n".join(lines).strip()


def journal_ticker_text(ticker, limit=15):
    ticker = str(ticker).upper().strip()
    events = trade_journal.by_ticker(ticker, limit=limit)

    if not events:
        return f"""
TRADE JOURNAL

No events found for:
{ticker}
""".strip()

    lines = ["TRADE JOURNAL", f"Ticker: {ticker}", ""]

    for event in reversed(events):
        timestamp = event.get("timestamp") or event.get("time")
        event_type = event.get("event") or event.get("event_type")
        payload = event.get("payload") or {}

        lines.append(f"{event_type}")
        lines.append(f"Time: {timestamp}")

        if payload:
            for key, value in payload.items():
                if key == "settings":
                    continue
                lines.append(f"{key}: {value}")

        lines.append("")

    return "\n".join(lines).strip()


def journal_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "Refresh Journal", "callback_data": "journal"}],
            [{"text": "Back", "callback_data": "main_menu"}],
        ]
    }