"""
Oracle Telegram Session UI

ORACLE-021.2

Purpose:
- Format Oracle session status.
- Format Oracle run-cycle results.
- Format Oracle menu.
- No execution.
- No direct Telegram sending.
"""


def oracle_home_text():
    return """
🔮 ORACLE AI

Autonomous Market Research

Status:
Research brain online.

Choose an Oracle tool below.
""".strip()


def oracle_home_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📊 Opportunity Feed", "callback_data": "oracle_feed"}],
            [{"text": "🔍 Run Research Cycle", "callback_data": "oracle_run"}],
            [{"text": "📈 Oracle Status", "callback_data": "oracle_status"}],
            [{"text": "👀 Watchlist", "callback_data": "oracle_watchlist"}],
            [{"text": "🧾 Signal Changes", "callback_data": "oracle_signal_changes"}],
            [{"text": "Back To Main Menu", "callback_data": "main_menu"}],
        ]
    }


def format_oracle_run_result(result):
    if not isinstance(result, dict):
        return "🔮 ORACLE RUN\n\nStatus:\nUnknown result."

    if result.get("status") == "BUSY":
        return f"""
🔮 ORACLE RUN

Status:
BUSY

Message:
{result.get("message", "Oracle is already running.")}
""".strip()

    if result.get("status") == "ERROR":
        return f"""
🔮 ORACLE RUN

Status:
ERROR

Error:
{result.get("error", "Unknown error")}
""".strip()

    summary = result.get("summary", {})

    return f"""
🔮 ORACLE RUN COMPLETE

Markets Scanned:
{summary.get("raw_markets_scanned", 0)}

Markets Discovered:
{summary.get("markets_discovered", 0)}

Added To Watchlist:
{summary.get("markets_added_to_watchlist", 0)}

Markets Researched:
{summary.get("markets_researched", 0)}

Queued Markets:
{summary.get("queued_markets", 0)}

Signal Changes:
{summary.get("signal_change_events", 0)}

Discovery Status:
{summary.get("discovery_status", "UNKNOWN")}

Research Status:
{summary.get("research_status", "UNKNOWN")}
""".strip()


def format_oracle_status_text(status):
    if not isinstance(status, dict):
        return "🔮 ORACLE STATUS\n\nStatus unavailable."

    summary = status.get("last_summary") or {}

    return f"""
🔮 ORACLE STATUS

State:
{status.get("status", "UNKNOWN")}

Last Started:
{status.get("last_started_at") or "Never"}

Last Finished:
{status.get("last_finished_at") or "Never"}

Last Error:
{status.get("last_error") or "None"}

Last Cycle Summary:

Markets Scanned:
{summary.get("raw_markets_scanned", 0)}

Markets Added:
{summary.get("markets_added_to_watchlist", 0)}

Markets Researched:
{summary.get("markets_researched", 0)}

Signal Changes:
{summary.get("signal_change_events", 0)}
""".strip()