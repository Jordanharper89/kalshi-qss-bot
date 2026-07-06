from pathlib import Path
from datetime import datetime

path = Path("telegram_bot.py")

if not path.exists():
    raise FileNotFoundError("telegram_bot.py not found. Run this from your bot folder.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

# Add import
import_line = "from oracle_market_intelligence import analyze_universe, format_top\n"
if import_line not in text:
    marker = "from oracle_dashboard_ui import (\n"
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find oracle_dashboard_ui import area.")
    text = text[:idx] + import_line + text[idx:]

# Add helper
helper = r'''

def build_oracle_market_intelligence_feed(limit=10):
    """
    ORACLE-040.4:
    Build live Oracle Top opportunities from Market Intelligence Engine.
    """
    try:
        analyze_universe(limit=500, top=50)
        return format_top(limit=limit)
    except Exception as e:
        return f"🧠 ORACLE MARKET INTELLIGENCE\n\nError building feed:\n{e}"


def send_oracle_market_intelligence_fast(chat_id):
    loading = send_message(
        chat_id,
        "🧠 ORACLE MARKET INTELLIGENCE\n\nStatus:\nBuilding live Top 10...",
        reply_markup=oracle_feed_keyboard(),
    )

    message_id = None
    try:
        message_id = loading.get("result", {}).get("message_id")
    except Exception:
        message_id = None

    def finish():
        message = build_oracle_market_intelligence_feed(limit=10)
        if message_id:
            edit_message(chat_id, message_id, message, reply_markup=oracle_feed_keyboard())
        else:
            send_message(chat_id, message, reply_markup=oracle_feed_keyboard())

    run_background(finish)


def edit_oracle_market_intelligence_fast(chat_id, message_id):
    edit_message(
        chat_id,
        message_id,
        "🧠 ORACLE MARKET INTELLIGENCE\n\nStatus:\nRefreshing live Top 10...",
        reply_markup=oracle_feed_keyboard(),
    )

    def finish():
        message = build_oracle_market_intelligence_feed(limit=10)
        edit_message(chat_id, message_id, message, reply_markup=oracle_feed_keyboard())

    run_background(finish)

'''

if "def build_oracle_market_intelligence_feed(limit=10):" not in text:
    marker = "\ndef main_settings_keyboard():"
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find helper insertion point before main_settings_keyboard.")
    text = text[:idx] + helper + text[idx:]

# Replace /oracle_feed command body
old_feed_cmd = '''    if text == "/oracle_feed":
        send_oracle_feed_fast(chat_id)
        return
'''
new_feed_cmd = '''    if text == "/oracle_feed":
        send_oracle_market_intelligence_fast(chat_id)
        return
'''
if old_feed_cmd in text:
    text = text.replace(old_feed_cmd, new_feed_cmd)

# Replace /oracle_top command body if current old block exists
old_top_cmd = '''    if text == "/oracle_top":
        from oracle_telegram import oracle_top_text, oracle_back_keyboard
        send_message(chat_id, oracle_top_text(limit=10), reply_markup=oracle_dashboard_back_keyboard())
        return
'''
new_top_cmd = '''    if text == "/oracle_top":
        send_oracle_market_intelligence_fast(chat_id)
        return
'''
if old_top_cmd in text:
    text = text.replace(old_top_cmd, new_top_cmd)

# Replace oracle_feed callback
old_feed_cb = '''    if data == "oracle_feed":
        answer_callback(callback_id, "Oracle feed")
        edit_oracle_feed_fast(chat_id, message_id)
        return
'''
new_feed_cb = '''    if data == "oracle_feed":
        answer_callback(callback_id, "Oracle feed")
        edit_oracle_market_intelligence_fast(chat_id, message_id)
        return
'''
if old_feed_cb in text:
    text = text.replace(old_feed_cb, new_feed_cb)

# Replace oracle_top callback
old_top_cb = '''    if data == "oracle_top":
        from oracle_telegram import oracle_top_text, oracle_back_keyboard
        answer_callback(callback_id, "Oracle top")
        edit_message(chat_id, message_id, oracle_top_text(limit=10), reply_markup=oracle_dashboard_back_keyboard())
        return
'''
new_top_cb = '''    if data == "oracle_top":
        answer_callback(callback_id, "Oracle top")
        edit_oracle_market_intelligence_fast(chat_id, message_id)
        return
'''
if old_top_cb in text:
    text = text.replace(old_top_cb, new_top_cb)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE-040.4 INSTALLED")
print(" Market Intelligence wired to Oracle Feed")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python telegram_bot.py")
print()
print("Telegram:")
print(" /oracle_feed")
print(" /oracle_top")