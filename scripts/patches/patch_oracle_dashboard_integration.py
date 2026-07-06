"""
Patch Oracle Dashboard Integration

ORACLE-024.3

Purpose:
- Integrate premium Oracle dashboard into telegram_bot.py
- Adds Oracle Dashboard command/callbacks
- Keeps existing bot intact
"""

from pathlib import Path
from datetime import datetime

BOT_FILE = Path("telegram_bot.py")

if not BOT_FILE.exists():
    raise FileNotFoundError("telegram_bot.py not found")

text = BOT_FILE.read_text(encoding="utf-8")

backup = Path(
    f"telegram_bot_backup_before_oracle_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
)
backup.write_text(text, encoding="utf-8")


# -------------------------------------------------
# 1. Add imports
# -------------------------------------------------

import_block = """
from oracle_dashboard_ui import (
    oracle_dashboard_text,
    oracle_dashboard_keyboard,
    oracle_premium_home_text,
    oracle_premium_home_keyboard,
)
"""

if "from oracle_dashboard_ui import" not in text:
    marker = "from dotenv import load_dotenv\n"
    text = text.replace(marker, marker + import_block + "\n")


# -------------------------------------------------
# 2. Add dashboard snapshot helper
# -------------------------------------------------

helper_code = r'''

def build_oracle_dashboard_snapshot():
    """
    Lightweight dashboard snapshot for Telegram UI.
    Uses available local files/services without breaking startup.
    """
    snapshot = {
        "health": {
            "healthy": True,
        },
        "scheduler": {
            "running": True,
            "cycles_completed": 0,
            "last_cycle": "Manual mode",
        },
        "metrics": {
            "total_cycles": 0,
            "markets_scanned": 0,
            "markets_researched": 0,
            "signal_changes": 0,
        },
        "opportunity_feed": [],
        "recent_alerts": [],
        "alert_statistics": {
            "total_alerts": 0,
        },
    }

    try:
        import json
        from pathlib import Path

        watch_file = Path("oracle_watchlist.json")
        if watch_file.exists():
            data = json.loads(watch_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                snapshot["metrics"]["markets_researched"] = len(data)
            elif isinstance(data, dict):
                snapshot["metrics"]["markets_researched"] = len(data)

        alert_file = Path("oracle_alert_history.json")
        if alert_file.exists():
            alerts = json.loads(alert_file.read_text(encoding="utf-8"))
            if isinstance(alerts, list):
                snapshot["recent_alerts"] = alerts[:10]
                snapshot["alert_statistics"]["total_alerts"] = len(alerts)

    except Exception:
        snapshot["health"]["healthy"] = False

    return snapshot


def oracle_placeholder_text(title):
    return f"""
━━━━━━━━━━━━━━━━━━━━━━
🔮 {title}
━━━━━━━━━━━━━━━━━━━━━━

Status:
This Oracle screen is connected and ready for the next build.

━━━━━━━━━━━━━━━━━━━━━━
""".strip()


def oracle_back_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "⬅ Back To Oracle", "callback_data": "oracle_menu"}],
            [{"text": "🏠 Main Menu", "callback_data": "main_menu"}],
        ]
    }
'''

if "def build_oracle_dashboard_snapshot():" not in text:
    marker = "def main_menu_text():"
    text = text.replace(marker, helper_code + "\n\n" + marker)


# -------------------------------------------------
# 3. Upgrade main menu Oracle button
# -------------------------------------------------

text = text.replace(
    '{"text": "Oracle Research", "callback_data": "oracle_menu"}',
    '{"text": "🔮 Oracle AI", "callback_data": "oracle_menu"}',
)


# -------------------------------------------------
# 4. Update help text
# -------------------------------------------------

text = text.replace(
    "/oracle = Oracle research menu",
    "/oracle = Oracle AI menu\n/oracle_dashboard = Oracle dashboard\n/oracle_feed = Top Oracle opportunities",
)


# -------------------------------------------------
# 5. Replace /oracle command screen
# -------------------------------------------------

old = '''    if text == "/oracle":
        from oracle_telegram import oracle_menu_text, oracle_menu_keyboard
        send_message(chat_id, oracle_menu_text(), reply_markup=oracle_menu_keyboard())
        return
'''

new = '''    if text == "/oracle":
        send_message(chat_id, oracle_premium_home_text(), reply_markup=oracle_premium_home_keyboard())
        return

    if text == "/oracle_dashboard":
        snapshot = build_oracle_dashboard_snapshot()
        send_message(chat_id, oracle_dashboard_text(snapshot), reply_markup=oracle_dashboard_keyboard())
        return
'''

if old in text:
    text = text.replace(old, new)


# -------------------------------------------------
# 6. Replace oracle_menu callback
# -------------------------------------------------

old = '''    if data == "oracle_menu":
        from oracle_telegram import oracle_menu_text, oracle_menu_keyboard
        answer_callback(callback_id, "Oracle")
        edit_message(chat_id, message_id, oracle_menu_text(), reply_markup=oracle_menu_keyboard())
        return
'''

new = '''    if data == "oracle_menu":
        answer_callback(callback_id, "Oracle")
        edit_message(chat_id, message_id, oracle_premium_home_text(), reply_markup=oracle_premium_home_keyboard())
        return

    if data == "oracle_dashboard":
        answer_callback(callback_id, "Dashboard")
        snapshot = build_oracle_dashboard_snapshot()
        edit_message(chat_id, message_id, oracle_dashboard_text(snapshot), reply_markup=oracle_dashboard_keyboard())
        return

    if data == "oracle_health":
        answer_callback(callback_id, "Health")
        snapshot = build_oracle_dashboard_snapshot()
        health = snapshot.get("health", {})
        text_out = f"""
❤️ ORACLE HEALTH

Healthy:
{health.get("healthy")}

Status:
Oracle dashboard layer is connected.
""".strip()
        edit_message(chat_id, message_id, text_out, reply_markup=oracle_back_keyboard())
        return

    if data == "oracle_metrics":
        answer_callback(callback_id, "Metrics")
        snapshot = build_oracle_dashboard_snapshot()
        metrics = snapshot.get("metrics", {})
        text_out = f"""
📈 ORACLE METRICS

Research Cycles:
{metrics.get("total_cycles", 0)}

Markets Scanned:
{metrics.get("markets_scanned", 0)}

Markets Researched:
{metrics.get("markets_researched", 0)}

Signal Changes:
{metrics.get("signal_changes", 0)}
""".strip()
        edit_message(chat_id, message_id, text_out, reply_markup=oracle_back_keyboard())
        return

    if data == "oracle_discovery":
        answer_callback(callback_id, "Discovery")
        edit_message(chat_id, message_id, oracle_placeholder_text("MARKET DISCOVERY"), reply_markup=oracle_back_keyboard())
        return

    if data == "oracle_signal_changes":
        answer_callback(callback_id, "Signal Changes")
        edit_message(chat_id, message_id, oracle_placeholder_text("SIGNAL CHANGES"), reply_markup=oracle_back_keyboard())
        return
'''

if old in text:
    text = text.replace(old, new)


BOT_FILE.write_text(text, encoding="utf-8")

print("Oracle dashboard integration patch complete.")
print(f"Backup created: {backup}")
print("Now run: python -m py_compile telegram_bot.py")