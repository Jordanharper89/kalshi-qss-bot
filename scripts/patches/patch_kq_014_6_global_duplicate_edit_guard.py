from pathlib import Path
from datetime import datetime

path = Path("telegram_bot.py")

if not path.exists():
    raise FileNotFoundError("telegram_bot.py not found. Run this from your bot folder.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

# Make sure duplicate edit guard imports exist.
import_line = "from oracle_message_cache import should_skip_dashboard_edit, remember_dashboard_edit\n"
if import_line not in text:
    marker = "from dotenv import load_dotenv\n"
    text = text.replace(marker, marker + import_line)

old = '''def edit_message(chat_id, message_id, text, reply_markup=None, track_nav=True):
    text = str(text or "No output.")
    final_markup = prepare_keyboard(chat_id, text, reply_markup) if reply_markup else None

    if track_nav:
        record_screen(chat_id, text, final_markup, push=True)

    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": format_for_telegram(text),
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    if final_markup:
        payload["reply_markup"] = final_markup

    try:
        _telegram_post("editMessageText", payload, timeout=8, queued=True)
    except Exception as e:
        print("Telegram edit error:", e)
'''

new = '''def edit_message(chat_id, message_id, text, reply_markup=None, track_nav=True):
    text = str(text or "No output.")
    final_markup = prepare_keyboard(chat_id, text, reply_markup) if reply_markup else None

    # KQ-014.6 / ORACLE-037.3:
    # Global duplicate edit guard.
    # If the exact same text + keyboard was already sent to this Telegram message,
    # skip the Telegram API call entirely.
    if should_skip_dashboard_edit(chat_id, message_id, text, final_markup):
        diag(f"KQ-014.6 skipped duplicate edit target={chat_id}:{message_id}")
        return

    if track_nav:
        record_screen(chat_id, text, final_markup, push=True)

    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": format_for_telegram(text),
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    if final_markup:
        payload["reply_markup"] = final_markup

    try:
        _telegram_post("editMessageText", payload, timeout=8, queued=True)
        remember_dashboard_edit(chat_id, message_id, text, final_markup)
    except Exception as e:
        print("Telegram edit error:", e)
'''

if old not in text:
    raise RuntimeError("Could not find exact edit_message function. Paste current edit_message if this fails.")

text = text.replace(old, new)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" KQ-014.6 INSTALLED")
print(" Global Duplicate Edit Guard")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python telegram_bot.py")
print()
print("Then tap Main Menu / Oracle Dashboard repeatedly.")
print("Expected CMD:")
print(" KQ-014.6 skipped duplicate edit target=...")