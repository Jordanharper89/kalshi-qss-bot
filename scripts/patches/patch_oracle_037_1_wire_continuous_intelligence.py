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
import_line = "import oracle_continuous_intelligence\n"
if import_line not in text:
    marker = "import oracle_dashboard_refresh\n"
    if marker in text:
        text = text.replace(marker, marker + import_line)
    else:
        text = import_line + text

# Add help command
if "/oracle_intel = Continuous intelligence status" not in text:
    text = text.replace(
        "/oracle_events = Recent Oracle event alerts\n",
        "/oracle_events = Recent Oracle event alerts\n/oracle_intel = Continuous intelligence status\n",
    )

# Add command handler
command_block = '''
    if text == "/oracle_intel":
        send_message(chat_id, oracle_continuous_intelligence.format_status(), reply_markup=oracle_dashboard_back_keyboard())
        return

'''

if 'if text == "/oracle_intel":' not in text:
    marker = '''    if text == "/oracle_events":
'''
    idx = text.find(marker)
    if idx == -1:
        marker = '''    if text == "/oracle_quality":
'''
        idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find Oracle command insertion point.")
    text = text[:idx] + command_block + text[idx:]

# Add callback handler
callback_block = '''
    if data == "oracle_intel":
        answer_callback(callback_id, "Intel")
        edit_message(chat_id, message_id, oracle_continuous_intelligence.format_status(), reply_markup=oracle_dashboard_back_keyboard())
        return

'''

if 'if data == "oracle_intel":' not in text:
    marker = '''    if data == "oracle_events":
'''
    idx = text.find(marker)
    if idx == -1:
        marker = '''    if data == "oracle_quality":
'''
        idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find Oracle callback insertion point.")
    text = text[:idx] + callback_block + text[idx:]

# Add Oracle Intel button to premium home keyboard by patching after function call is harder,
# so add a safe wrapper that appends the button only if possible.
wrapper = r'''

# ==============================
# ORACLE-037.1 CONTINUOUS INTELLIGENCE UI PATCH
# ==============================

try:
    _original_oracle_premium_home_keyboard = oracle_premium_home_keyboard

    def oracle_premium_home_keyboard():
        kb = _original_oracle_premium_home_keyboard()
        rows = kb.setdefault("inline_keyboard", [])

        exists = False
        for row in rows:
            for btn in row:
                if btn.get("callback_data") == "oracle_intel":
                    exists = True

        if not exists:
            rows.insert(1, [{"text": "🧠 Continuous Intelligence", "callback_data": "oracle_intel"}])

        return kb

    print("[ORACLE-037.1] Oracle Continuous Intelligence button installed")

except Exception as e:
    print(f"[ORACLE-037.1] UI button patch error: {e}")

'''

if "ORACLE-037.1 CONTINUOUS INTELLIGENCE UI PATCH" not in text:
    insert_marker = '\ndef main():\n'
    idx = text.find(insert_marker)
    if idx == -1:
        raise RuntimeError("Could not find main() insertion point.")
    text = text[:idx] + wrapper + text[idx:]

# Start continuous intelligence in main after start_position_monitor
start_marker = "    start_position_monitor(send_message_fn=send_message, chat_id=CHAT_ID)\n"
start_block = '''    try:
        oracle_continuous_intelligence.start(interval_seconds=10)
    except Exception as e:
        print(f"[ORACLE-037.1] continuous intelligence start error: {e}")

'''

if "oracle_continuous_intelligence.start(interval_seconds=10)" not in text:
    if start_marker not in text:
        raise RuntimeError("Could not find startup insertion point.")
    text = text.replace(start_marker, start_marker + start_block)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE-037.1 INSTALLED")
print(" Continuous Intelligence wired into Telegram")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python telegram_bot.py")
print()
print("Telegram:")
print(" /oracle_intel")
print()
print("Expected CMD:")
print(" [ORACLE-037] Continuous Intelligence Pipeline started interval=10s")