from pathlib import Path
from datetime import datetime

path = Path("telegram_bot.py")

if not path.exists():
    raise FileNotFoundError("telegram_bot.py not found. Run this from your bot folder.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

import_block = """from oracle_event_alert_ui import recent_event_alerts_text, event_alert_keyboard\n"""

if import_block not in text:
    marker = "from oracle_dashboard_ui import (\n"
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find oracle_dashboard_ui import area.")
    text = text[:idx] + import_block + text[idx:]

# Add command to help text if missing
if "/oracle_events = Recent Oracle event alerts" not in text:
    text = text.replace(
        "/oracle_quality = Oracle data quality\n",
        "/oracle_quality = Oracle data quality\n/oracle_events = Recent Oracle event alerts\n",
    )

# Add /oracle_events command
command_block = '''
    if text == "/oracle_events":
        send_message(chat_id, recent_event_alerts_text(limit=10), reply_markup=event_alert_keyboard())
        return

'''

if 'if text == "/oracle_events":' not in text:
    marker = '''    if text == "/oracle_quality":
'''
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find /oracle_quality command area.")
    text = text[:idx] + command_block + text[idx:]

# Add callbacks
callback_block = '''
    if data == "oracle_events":
        answer_callback(callback_id, "Events")
        edit_message(chat_id, message_id, recent_event_alerts_text(limit=10), reply_markup=event_alert_keyboard())
        return

    if data == "oracle_events_high":
        answer_callback(callback_id, "High events")
        edit_message(chat_id, message_id, recent_event_alerts_text(limit=10, priority="HIGH"), reply_markup=event_alert_keyboard())
        return

    if data == "oracle_events_medium":
        answer_callback(callback_id, "Medium events")
        edit_message(chat_id, message_id, recent_event_alerts_text(limit=10, priority="MEDIUM"), reply_markup=event_alert_keyboard())
        return

    if data == "oracle_events_low":
        answer_callback(callback_id, "Low events")
        edit_message(chat_id, message_id, recent_event_alerts_text(limit=10, priority="LOW"), reply_markup=event_alert_keyboard())
        return

'''

if 'if data == "oracle_events":' not in text:
    marker = '''    if data == "oracle_quality":
'''
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find oracle_quality callback area.")
    text = text[:idx] + callback_block + text[idx:]

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE-035.1 INSTALLED")
print(" Event Alerts wired into Telegram")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python telegram_bot.py")
print()
print("Telegram:")
print(" /oracle_events")