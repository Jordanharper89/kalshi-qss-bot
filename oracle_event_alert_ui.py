"""
ORACLE-035 — Event Alert UI

Purpose:
- Turn ORACLE-034 detected events into clean Telegram alert cards
- Format recent events
- Filter by priority
- Keep this as UI only: no trading/execution logic
"""

import time

from oracle_event_detection import get_recent_events


def _fmt_time(ts):
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(ts)))
    except Exception:
        return "Unknown"


def event_priority_icon(priority):
    priority = str(priority or "").upper()

    if priority == "HIGH":
        return "🔴"
    if priority == "MEDIUM":
        return "🟡"
    if priority == "LOW":
        return "🟢"

    return "⚪"


def format_value(value):
    if value is None:
        return "N/A"

    if isinstance(value, float):
        return round(value, 4)

    return value


def event_alert_card(event):
    priority = str(event.get("priority") or "UNKNOWN").upper()
    icon = event_priority_icon(priority)

    return f"""
{icon} ORACLE EVENT ALERT

Priority:
{priority}

Type:
{event.get("event_type", "UNKNOWN")}

Ticker:
{event.get("ticker", "UNKNOWN")}

Title:
{event.get("title", "Unknown Market")}

Field:
{event.get("field", "N/A")}

Old:
{format_value(event.get("old"))}

New:
{format_value(event.get("new"))}

Delta:
{format_value(event.get("delta", event.get("delta_pct", "N/A")))}

Message:
{event.get("message", "No message.")}

Detected:
{_fmt_time(event.get("timestamp"))}
""".strip()


def recent_event_alerts_text(limit=10, priority=None):
    events = get_recent_events(limit=limit, priority=priority)

    if not events:
        label = f"{priority} priority " if priority else ""
        return f"No recent {label}Oracle events."

    header = "🔔 ORACLE EVENT ALERTS"

    if priority:
        header += f"\nPriority Filter: {str(priority).upper()}"

    cards = [event_alert_card(event) for event in events]

    return header + "\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n" + "\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n".join(cards)


def event_alert_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "Refresh Events", "callback_data": "oracle_events"}],
            [
                {"text": "High", "callback_data": "oracle_events_high"},
                {"text": "Medium", "callback_data": "oracle_events_medium"},
                {"text": "Low", "callback_data": "oracle_events_low"},
            ],
            [{"text": "Oracle Menu", "callback_data": "oracle_menu"}],
            [{"text": "Main Menu", "callback_data": "main_menu"}],
        ]
    }


def diagnostics():
    return {
        "module": "oracle_event_alert_ui",
        "status": "ok",
        "recent_events": len(get_recent_events(limit=20)),
    }


if __name__ == "__main__":
    print(recent_event_alerts_text(limit=5))
