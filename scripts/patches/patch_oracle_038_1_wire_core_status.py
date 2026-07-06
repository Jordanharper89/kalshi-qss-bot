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
if "import oracle_core\n" not in text:
    marker = "import oracle_continuous_intelligence\n"
    if marker in text:
        text = text.replace(marker, marker + "import oracle_core\n")
    else:
        text = "import oracle_core\n" + text

# Add help text
if "/oracle_core = Oracle core status" not in text:
    text = text.replace(
        "/oracle_intel = Continuous intelligence status\n",
        "/oracle_intel = Continuous intelligence status\n/oracle_core = Oracle core status\n",
    )

# Add command
command_block = '''
    if text == "/oracle_core":
        send_message(chat_id, oracle_core.format_status(), reply_markup=oracle_dashboard_back_keyboard())
        return

'''

if 'if text == "/oracle_core":' not in text:
    marker = '''    if text == "/oracle_intel":
'''
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find /oracle_intel insertion point.")
    text = text[:idx] + command_block + text[idx:]

# Add callback
callback_block = '''
    if data == "oracle_core":
        answer_callback(callback_id, "Core")
        edit_message(chat_id, message_id, oracle_core.format_status(), reply_markup=oracle_dashboard_back_keyboard())
        return

'''

if 'if data == "oracle_core":' not in text:
    marker = '''    if data == "oracle_intel":
'''
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find oracle_intel callback insertion point.")
    text = text[:idx] + callback_block + text[idx:]

# Add Oracle Core button to Oracle menu wrapper if the ORACLE-037.1 wrapper exists
if 'callback_data") == "oracle_core"' not in text:
    old = '''        if not exists:
            rows.insert(1, [{"text": "🧠 Continuous Intelligence", "callback_data": "oracle_intel"}])
'''
    new = '''        if not exists:
            rows.insert(1, [{"text": "🧠 Continuous Intelligence", "callback_data": "oracle_intel"}])

        core_exists = False
        for row in rows:
            for btn in row:
                if btn.get("callback_data") == "oracle_core":
                    core_exists = True

        if not core_exists:
            rows.insert(2, [{"text": "🧩 Oracle Core", "callback_data": "oracle_core"}])
'''
    if old in text:
        text = text.replace(old, new)
    else:
        print("Warning: Could not find Oracle menu wrapper button block. Command still installed.")

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE-038.1 INSTALLED")
print(" Core Status wired into Telegram")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python telegram_bot.py")
print()
print("Telegram:")
print(" /oracle_core")