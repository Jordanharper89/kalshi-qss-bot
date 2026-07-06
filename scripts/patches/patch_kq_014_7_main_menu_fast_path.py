from pathlib import Path
from datetime import datetime

path = Path("telegram_bot.py")

if not path.exists():
    raise FileNotFoundError("telegram_bot.py not found. Run this from your bot folder.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

helper = r'''

def edit_main_menu_fast(chat_id, message_id):
    """
    KQ-014.7:
    Fast main menu path with duplicate protection.
    """
    edit_message(
        chat_id,
        message_id,
        main_menu_text(),
        reply_markup=main_menu_keyboard(),
        track_nav=False,
    )

'''

if "def edit_main_menu_fast(chat_id, message_id):" not in text:
    marker = "\ndef oracle_feed_keyboard():"
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find insertion point before oracle_feed_keyboard.")
    text = text[:idx] + helper + text[idx:]

old = '''    if data == "main_menu":
        answer_callback(callback_id, "Main menu")
        clear_navigation(chat_id)
        edit_message(chat_id, message_id, main_menu_text(), reply_markup=main_menu_keyboard(), track_nav=False)
        return
'''

new = '''    if data == "main_menu":
        answer_callback(callback_id, "Main menu")
        clear_navigation(chat_id)
        edit_main_menu_fast(chat_id, message_id)
        return
'''

if old not in text:
    raise RuntimeError("Could not find main_menu callback block.")

text = text.replace(old, new)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" KQ-014.7 INSTALLED")
print(" Main Menu Fast Path")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python telegram_bot.py")
print()
print("Telegram:")
print(" Tap Main Menu repeatedly")
print()
print("Expected:")
print(" Duplicate taps should skip edit or complete faster.")