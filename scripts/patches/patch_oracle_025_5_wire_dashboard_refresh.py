from pathlib import Path
from datetime import datetime
import re

path = Path("telegram_bot.py")

if not path.exists():
    raise FileNotFoundError("telegram_bot.py not found. Run this from your bot folder.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

# Fix bad object-style import.
text = text.replace(
    "from oracle_dashboard_refresh import oracle_dashboard_refresh\n",
    "import oracle_dashboard_refresh\n",
)

# Add dashboard cache imports if missing.
if "from oracle_message_cache import should_skip_dashboard_edit, remember_dashboard_edit" not in text:
    marker = "from dotenv import load_dotenv\n"
    text = text.replace(
        marker,
        marker + "from oracle_message_cache import should_skip_dashboard_edit, remember_dashboard_edit\n",
    )

# Add helper functions after build_oracle_dashboard_snapshot.
helper = r'''

def build_oracle_dashboard_screen():
    """
    ORACLE-025.5:
    Returns ready-to-send dashboard text + keyboard.
    Uses background refresh snapshot when available.
    Falls back to direct build safely.
    """
    try:
        snap = oracle_dashboard_refresh.get_snapshot()

        if snap and snap.get("ok") and snap.get("text"):
            return snap.get("text"), snap.get("reply_markup") or oracle_dashboard_keyboard()

    except Exception as e:
        print(f"[ORACLE-025.5] dashboard refresh snapshot error: {e}")

    snapshot = build_oracle_dashboard_snapshot()
    return oracle_dashboard_text(snapshot), oracle_dashboard_keyboard()


def edit_oracle_dashboard_fast(chat_id, message_id):
    """
    ORACLE-025.5:
    Edit dashboard only when content changed.
    """
    text_out, keyboard = build_oracle_dashboard_screen()

    if should_skip_dashboard_edit(chat_id, message_id, text_out, keyboard):
        diag("[ORACLE-025.5] skipped duplicate Oracle dashboard edit")
        return

    edit_message(chat_id, message_id, text_out, reply_markup=keyboard)
    remember_dashboard_edit(chat_id, message_id, text_out, keyboard)


def send_oracle_dashboard_fast(chat_id):
    """
    ORACLE-025.5:
    Send dashboard from cached/background snapshot.
    """
    text_out, keyboard = build_oracle_dashboard_screen()
    send_message(chat_id, text_out, reply_markup=keyboard)

'''

if "def build_oracle_dashboard_screen():" not in text:
    insert_after = "def oracle_placeholder_text(title):"
    idx = text.find(insert_after)
    if idx == -1:
        raise RuntimeError("Could not find oracle_placeholder_text insertion point.")
    text = text[:idx] + helper + "\n" + text[idx:]

# Replace command dashboard direct build.
old = '''    if text == "/oracle_dashboard":
        snapshot = build_oracle_dashboard_snapshot()
        send_message(chat_id, oracle_dashboard_text(snapshot), reply_markup=oracle_dashboard_keyboard())
        return
'''
new = '''    if text == "/oracle_dashboard":
        send_oracle_dashboard_fast(chat_id)
        return
'''
text = text.replace(old, new)

# Replace callback dashboard direct build.
old = '''    if data == "oracle_dashboard":
        answer_callback(callback_id, "Dashboard")
        snapshot = build_oracle_dashboard_snapshot()
        edit_message(chat_id, message_id, oracle_dashboard_text(snapshot), reply_markup=oracle_dashboard_keyboard())
        return
'''
new = '''    if data == "oracle_dashboard":
        answer_callback(callback_id, "Dashboard")
        edit_oracle_dashboard_fast(chat_id, message_id)
        return
'''
text = text.replace(old, new)

# Start dashboard refresh in main after Telegram queue starts.
start_line = "    start_telegram_queue(BASE, diag_fn=diag)\n"
refresh_start = '''    try:
        oracle_dashboard_refresh.start_dashboard_refresh(
            lambda: (oracle_dashboard_text(build_oracle_dashboard_snapshot()), oracle_dashboard_keyboard())
        )
    except Exception as e:
        print(f"[ORACLE-025.5] dashboard refresh start error: {e}")

'''

if "start_dashboard_refresh(" not in text:
    text = text.replace(start_line, start_line + refresh_start)

path.write_text(text, encoding="utf-8")

print("✅ ORACLE-025.5 wired into telegram_bot.py")
print(f"Backup created: {backup.name}")
print("")
print("Now test:")
print("python telegram_bot.py")
print("")
print("Then in Telegram:")
print("/oracle_dashboard")
print("Tap Dashboard repeatedly and watch CMD for:")
print("[ORACLE-025.5] skipped duplicate Oracle dashboard edit")