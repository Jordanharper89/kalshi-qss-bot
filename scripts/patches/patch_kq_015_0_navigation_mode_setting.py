from pathlib import Path
from datetime import datetime

path = Path("telegram_bot.py")

if not path.exists():
    raise FileNotFoundError("telegram_bot.py not found. Run this from your bot folder.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

# Add setting near FAST UI settings.
setting = '''
# KQ-015.0 Navigation Mode
# resend = send new menu first, delete old menu after
# edit = old behavior, edit existing message
NAVIGATION_MODE = os.getenv("KQ_NAVIGATION_MODE", "resend").strip().lower()
'''

if "NAVIGATION_MODE = os.getenv" not in text:
    marker = "FAST_UI_SKIP_LOW_RISK_CALLBACK_ANSWERS = os.getenv"
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find FAST_UI_SKIP_LOW_RISK_CALLBACK_ANSWERS setting.")
    line_end = text.find("\n", idx)
    text = text[:line_end + 1] + setting + text[line_end + 1:]

old = '''def replace_with_main_menu_fast(chat_id, message_id):
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

new = '''def replace_with_main_menu_fast(chat_id, message_id):
    """
    KQ-015.0:
    Main menu navigation mode.

    resend:
        Send new Main Menu first, delete old message after.
    edit:
        Edit the existing message.
    """
    clear_navigation(chat_id)

    if NAVIGATION_MODE == "edit":
        edit_main_menu_fast(chat_id, message_id)
        return

    send_message(
        chat_id,
        main_menu_text(),
        reply_markup=main_menu_keyboard(),
        track_nav=False,
    )

    delete_message_fast(chat_id, message_id)

'''

if old not in text:
    raise RuntimeError("Could not find KQ-014.9 replace_with_main_menu_fast block.")

text = text.replace(old, new)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" KQ-015.0 INSTALLED")
print(" Navigation Mode Setting")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Default mode:")
print(" resend")
print()
print("Optional .env setting:")
print(" KQ_NAVIGATION_MODE=edit")
print()
print("Test:")
print(" python telegram_bot.py")