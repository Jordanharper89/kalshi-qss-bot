from pathlib import Path
from datetime import datetime

path = Path("telegram_bot.py")

if not path.exists():
    raise FileNotFoundError("telegram_bot.py not found. Run this from your bot folder.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

old = '''def delete_message_fast(chat_id, message_id):
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

new = '''def delete_message_fast(chat_id, message_id):
    """
    KQ-014.9:
    Queue deleteMessage without blocking.
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
    KQ-014.9:
    Fast main menu navigation.

    Sends the new Main Menu immediately, then queues deletion of the old menu.
    This makes the screen feel faster because the user sees the new menu before
    Telegram finishes deleting/editing the old message.
    """
    clear_navigation(chat_id)

    send_message(
        chat_id,
        main_menu_text(),
        reply_markup=main_menu_keyboard(),
        track_nav=False,
    )

    delete_message_fast(chat_id, message_id)

'''

if old not in text:
    raise RuntimeError("Could not find KQ-014.8 helper block.")

text = text.replace(old, new)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" KQ-014.9 INSTALLED")
print(" Navigation Cleanup")
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
print(" New Main Menu sends first, old message deletes after.")