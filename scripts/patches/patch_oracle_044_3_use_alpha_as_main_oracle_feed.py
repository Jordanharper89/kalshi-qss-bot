from pathlib import Path
from datetime import datetime

path = Path("telegram_bot.py")

if not path.exists():
    raise FileNotFoundError("telegram_bot.py not found.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

old = '''    if text == "/oracle_feed":
        send_oracle_market_intelligence_fast(chat_id)
        return
'''

new = '''    if text == "/oracle_feed":
        send_oracle_alpha_fast(chat_id)
        return
'''

if old in text:
    text = text.replace(old, new)
else:
    print("Warning: /oracle_feed command block not found or already patched.")

old2 = '''    if text == "/oracle_top":
        send_oracle_market_intelligence_fast(chat_id)
        return
'''

new2 = '''    if text == "/oracle_top":
        send_oracle_alpha_fast(chat_id)
        return
'''

if old2 in text:
    text = text.replace(old2, new2)
else:
    print("Warning: /oracle_top command block not found or already patched.")

old3 = '''    if data == "oracle_feed":
        answer_callback(callback_id, "Oracle feed")
        edit_oracle_market_intelligence_fast(chat_id, message_id)
        return
'''

new3 = '''    if data == "oracle_feed":
        answer_callback(callback_id, "Oracle feed")
        edit_oracle_alpha_fast(chat_id, message_id)
        return
'''

if old3 in text:
    text = text.replace(old3, new3)
else:
    print("Warning: oracle_feed callback block not found or already patched.")

old4 = '''    if data == "oracle_top":
        answer_callback(callback_id, "Oracle top")
        edit_oracle_market_intelligence_fast(chat_id, message_id)
        return
'''

new4 = '''    if data == "oracle_top":
        answer_callback(callback_id, "Oracle top")
        edit_oracle_alpha_fast(chat_id, message_id)
        return
'''

if old4 in text:
    text = text.replace(old4, new4)
else:
    print("Warning: oracle_top callback block not found or already patched.")

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE-044.3 INSTALLED")
print(" Alpha Discovery is now main Oracle Feed")
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
print(" /oracle_alpha")