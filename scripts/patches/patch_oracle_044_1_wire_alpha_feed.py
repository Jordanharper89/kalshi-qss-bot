from pathlib import Path
from datetime import datetime

path = Path("telegram_bot.py")

if not path.exists():
    raise FileNotFoundError("telegram_bot.py not found.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

import_line = "from oracle_alpha_discovery import run_alpha_discovery, format_top_alpha\n"
if import_line not in text:
    text = import_line + text

helper = r'''

def build_oracle_alpha_feed(limit=10):
    try:
        run_alpha_discovery(limit=50)
        return format_top_alpha(limit=limit)
    except Exception as e:
        return f"⚡ ORACLE ALPHA DISCOVERY\n\nError:\n{e}"


def send_oracle_alpha_fast(chat_id):
    loading = send_message(
        chat_id,
        "⚡ ORACLE ALPHA DISCOVERY\n\nStatus:\nBuilding live alpha feed...",
        reply_markup=oracle_feed_keyboard(),
    )

    message_id = None
    try:
        message_id = loading.get("result", {}).get("message_id")
    except Exception:
        pass

    def finish():
        msg = build_oracle_alpha_feed(limit=10)
        if message_id:
            edit_message(chat_id, message_id, msg, reply_markup=oracle_feed_keyboard())
        else:
            send_message(chat_id, msg, reply_markup=oracle_feed_keyboard())

    run_background(finish)


def edit_oracle_alpha_fast(chat_id, message_id):
    edit_message(
        chat_id,
        message_id,
        "⚡ ORACLE ALPHA DISCOVERY\n\nStatus:\nRefreshing alpha feed...",
        reply_markup=oracle_feed_keyboard(),
    )

    def finish():
        edit_message(
            chat_id,
            message_id,
            build_oracle_alpha_feed(limit=10),
            reply_markup=oracle_feed_keyboard(),
        )

    run_background(finish)

'''

if "def build_oracle_alpha_feed(limit=10):" not in text:
    marker = "\ndef build_oracle_market_intelligence_feed(limit=10):"
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find Market Intelligence helper insertion point.")
    text = text[:idx] + helper + text[idx:]

# Add help text
if "/oracle_alpha = Oracle alpha discovery" not in text:
    text = text.replace(
        "/oracle_top = Oracle top opportunities\n",
        "/oracle_top = Oracle top opportunities\n/oracle_alpha = Oracle alpha discovery\n",
    )

# Add command
cmd = '''
    if text == "/oracle_alpha":
        send_oracle_alpha_fast(chat_id)
        return

'''

if 'if text == "/oracle_alpha":' not in text:
    marker = '''    if text == "/oracle_feed":'''
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find /oracle_feed command insertion point.")
    text = text[:idx] + cmd + text[idx:]

# Add callback
cb = '''
    if data == "oracle_alpha":
        answer_callback(callback_id, "Alpha")
        edit_oracle_alpha_fast(chat_id, message_id)
        return

'''

if 'if data == "oracle_alpha":' not in text:
    marker = '''    if data == "oracle_feed":'''
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find oracle_feed callback insertion point.")
    text = text[:idx] + cb + text[idx:]

# Add Alpha button into Oracle premium keyboard wrapper if present
old = '''        if not core_exists:
            rows.insert(2, [{"text": "🧩 Oracle Core", "callback_data": "oracle_core"}])
'''

new = '''        if not core_exists:
            rows.insert(2, [{"text": "🧩 Oracle Core", "callback_data": "oracle_core"}])

        alpha_exists = False
        for row in rows:
            for btn in row:
                if btn.get("callback_data") == "oracle_alpha":
                    alpha_exists = True

        if not alpha_exists:
            rows.insert(1, [{"text": "⚡ Alpha Discovery", "callback_data": "oracle_alpha"}])
'''

if old in text and "callback_data\") == \"oracle_alpha\"" not in text:
    text = text.replace(old, new)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE-044.1 INSTALLED")
print(" Alpha Discovery wired into Telegram")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python telegram_bot.py")
print()
print("Telegram:")
print(" /oracle_alpha")