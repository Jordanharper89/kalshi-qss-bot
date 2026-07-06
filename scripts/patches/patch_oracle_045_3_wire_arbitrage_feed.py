from pathlib import Path
from datetime import datetime

path = Path("telegram_bot.py")

if not path.exists():
    raise FileNotFoundError("telegram_bot.py not found.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

import_line = "from oracle_cross_market_arbitrage import run_arbitrage_scan, format_top_arbitrage\n"
if import_line not in text:
    text = import_line + text

helper = r'''

def build_oracle_arbitrage_feed(limit=10):
    try:
        run_arbitrage_scan()
        return format_top_arbitrage(limit=limit)
    except Exception as e:
        return f"⚡ ORACLE ARBITRAGE\n\nError:\n{e}"


def send_oracle_arbitrage_fast(chat_id):
    loading = send_message(
        chat_id,
        "⚡ ORACLE ARBITRAGE\n\nStatus:\nScanning cross-market pricing...",
        reply_markup=oracle_feed_keyboard(),
    )

    message_id = None
    try:
        message_id = loading.get("result", {}).get("message_id")
    except Exception:
        pass

    def finish():
        msg = build_oracle_arbitrage_feed(limit=10)
        if message_id:
            edit_message(chat_id, message_id, msg, reply_markup=oracle_feed_keyboard())
        else:
            send_message(chat_id, msg, reply_markup=oracle_feed_keyboard())

    run_background(finish)


def edit_oracle_arbitrage_fast(chat_id, message_id):
    edit_message(
        chat_id,
        message_id,
        "⚡ ORACLE ARBITRAGE\n\nStatus:\nRefreshing cross-market scan...",
        reply_markup=oracle_feed_keyboard(),
    )

    def finish():
        edit_message(
            chat_id,
            message_id,
            build_oracle_arbitrage_feed(limit=10),
            reply_markup=oracle_feed_keyboard(),
        )

    run_background(finish)

'''

if "def build_oracle_arbitrage_feed(limit=10):" not in text:
    marker = "\ndef build_oracle_alpha_feed(limit=10):"
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find alpha helper insertion point.")
    text = text[:idx] + helper + text[idx:]

if "/oracle_arbitrage = Oracle cross-market arbitrage" not in text:
    text = text.replace(
        "/oracle_alpha = Oracle alpha discovery\n",
        "/oracle_alpha = Oracle alpha discovery\n/oracle_arbitrage = Oracle cross-market arbitrage\n",
    )

cmd = '''
    if text == "/oracle_arbitrage":
        send_oracle_arbitrage_fast(chat_id)
        return

'''

if 'if text == "/oracle_arbitrage":' not in text:
    marker = '''    if text == "/oracle_alpha":'''
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find /oracle_alpha command insertion point.")
    text = text[:idx] + cmd + text[idx:]

cb = '''
    if data == "oracle_arbitrage":
        answer_callback(callback_id, "Arbitrage")
        edit_oracle_arbitrage_fast(chat_id, message_id)
        return

'''

if 'if data == "oracle_arbitrage":' not in text:
    marker = '''    if data == "oracle_alpha":'''
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find oracle_alpha callback insertion point.")
    text = text[:idx] + cb + text[idx:]

# Add button after Alpha button if wrapper exists
old = '''        if not alpha_exists:
            rows.insert(1, [{"text": "⚡ Alpha Discovery", "callback_data": "oracle_alpha"}])
'''

new = '''        if not alpha_exists:
            rows.insert(1, [{"text": "⚡ Alpha Discovery", "callback_data": "oracle_alpha"}])

        arb_exists = False
        for row in rows:
            for btn in row:
                if btn.get("callback_data") == "oracle_arbitrage":
                    arb_exists = True

        if not arb_exists:
            rows.insert(2, [{"text": "⚖️ Arbitrage Scan", "callback_data": "oracle_arbitrage"}])
'''

if old in text and 'callback_data") == "oracle_arbitrage"' not in text:
    text = text.replace(old, new)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE-045.3 INSTALLED")
print(" Arbitrage Feed wired into Telegram")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python telegram_bot.py")
print()
print("Telegram:")
print(" /oracle_arbitrage")