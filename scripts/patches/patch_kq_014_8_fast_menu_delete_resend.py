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

def delete_message_fast(chat_id, message_id):
    """
    KQ-014.8:
    Delete old Telegram message without blocking navigation.
    """
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
    }

    try:
        _telegram_post("deleteMessage", payload, timeout=3, queued=True)
    except Exception as e:
        print(f"Telegram delete error: {e}")


def replace_with_main_menu_fast(chat_id, message_id):
    """
    KQ-014.8:
    For main menu navigation, sending a fresh message can feel faster than waiting
    on Telegram editMessageText when Telegram edits are slow.
    """
    clear_navigation(chat_id)
    delete_message_fast(chat_id, message_id)
    send_message(
        chat_id,
        main_menu_text(),
        reply_markup=main_menu_keyboard(),
        track_nav=False,
    )

'''

if "def replace_with_main_menu_fast(chat_id, message_id):" not in text:
    marker = "\ndef edit_main_menu_fast(chat_id, message_id):"
    idx = text.find(marker)
    if idx == -1:
        marker = "\ndef oracle_feed_keyboard():"
        idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find insertion point.")
    text = text[:idx] + helper + text[idx:]

old = '''    if data == "main_menu":
        answer_callback(callback_id, "Main menu")
        clear_navigation(chat_id)
        edit_main_menu_fast(chat_id, message_id)
        return
'''

new = '''    if data == "main_menu":
        answer_callback(callback_id, "Main menu")
        replace_with_main_menu_fast(chat_id, message_id)
        return
'''

if old not in text:
    raise RuntimeError("Could not find KQ-014.7 main_menu block. Run KQ-014.7 first or paste callback section.")

text = text.replace(old, new)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" KQ-014.8 INSTALLED")
print(" Fast Menu Delete + Resend")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python telegram_bot.py")
print()
print("Telegram:")
print(" Tap Main Menu")
print()
print("Expected:")
print(" A fresh Main Menu message appears faster than waiting on slow editMessageText.")