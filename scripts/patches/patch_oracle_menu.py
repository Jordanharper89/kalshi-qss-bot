from pathlib import Path
import re

path = Path("telegram_bot.py")
text = path.read_text(encoding="utf-8")

backup = Path("telegram_bot_backup_before_oracle.py")
backup.write_text(text, encoding="utf-8")

text = re.sub(
    r'def main_menu_text\(\):.*?def main_settings_keyboard\(\):',
    '''def main_menu_text():
    return """
Q SERIES COMMAND CENTER

/oracle = Oracle research
/check = Scan market
/positions = Open positions
/orders = Open orders
/settings = Trade settings
/balance = Account balance
/help = Help
""".strip()


def main_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "Oracle Research", "callback_data": "oracle_menu"}],
            [{"text": "Scan Market", "callback_data": "main_check"}],
            [{"text": "Positions", "callback_data": "positions_main"}],
            [{"text": "Open Orders", "callback_data": "main_orders"}],
            [{"text": "Settings", "callback_data": "settings_main"}],
            [{"text": "Balance", "callback_data": "main_balance"}],
        ]
    }


def main_settings_keyboard():''',
    text,
    flags=re.S,
)

text = re.sub(
    r'def help_text\(\):.*?def handle_waiting_input\(chat_id, text\):',
    '''def help_text():
    return """
Q SERIES COMMANDS

Core:
/menu = Main menu
/oracle = Oracle research menu
/oracle_top = Top Oracle signals
/oracle_quality = Oracle data quality
/oracle_signal TICKER = Oracle signal detail

Execution:
/check = Scan Kalshi ticker/link
/positions = View positions
/orders = Open orders
/settings = Trade settings
/balance = Kalshi balance

Old scanners have been removed from the command menu.
""".strip()


def handle_waiting_input(chat_id, text):''',
    text,
    flags=re.S,
)

old_command_block = '''    if text == "/settings":
        send_message(chat_id, format_settings(), reply_markup=main_settings_keyboard())
        return
'''

new_command_block = '''    if text == "/oracle":
        from oracle_telegram import oracle_menu_text, oracle_menu_keyboard
        send_message(chat_id, oracle_menu_text(), reply_markup=oracle_menu_keyboard())
        return

    if text == "/oracle_top":
        from oracle_telegram import oracle_top_text, oracle_back_keyboard
        send_message(chat_id, oracle_top_text(limit=10), reply_markup=oracle_back_keyboard())
        return

    if text == "/oracle_quality":
        from oracle_telegram import oracle_quality_text, oracle_back_keyboard
        send_message(chat_id, oracle_quality_text(), reply_markup=oracle_back_keyboard())
        return

    if text.startswith("/oracle_signal"):
        from oracle_telegram import oracle_signal_text, oracle_back_keyboard
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_message(chat_id, "Send it like this:\\n/oracle_signal TICKER")
        else:
            send_message(chat_id, oracle_signal_text(parts[1]), reply_markup=oracle_back_keyboard())
        return

    if text == "/settings":
        send_message(chat_id, format_settings(), reply_markup=main_settings_keyboard())
        return
'''

text = text.replace(old_command_block, new_command_block)

callback_insert_after = '''    if data == "main_menu":
        answer_callback(callback_id, "Main menu")
        clear_navigation(chat_id)
        edit_message(chat_id, message_id, main_menu_text(), reply_markup=main_menu_keyboard(), track_nav=False)
        return
'''

callback_oracle_block = '''    if data == "main_menu":
        answer_callback(callback_id, "Main menu")
        clear_navigation(chat_id)
        edit_message(chat_id, message_id, main_menu_text(), reply_markup=main_menu_keyboard(), track_nav=False)
        return

    if data == "oracle_menu":
        from oracle_telegram import oracle_menu_text, oracle_menu_keyboard
        answer_callback(callback_id, "Oracle")
        edit_message(chat_id, message_id, oracle_menu_text(), reply_markup=oracle_menu_keyboard())
        return

    if data == "oracle_top":
        from oracle_telegram import oracle_top_text, oracle_back_keyboard
        answer_callback(callback_id, "Oracle top")
        edit_message(chat_id, message_id, oracle_top_text(limit=10), reply_markup=oracle_back_keyboard())
        return

    if data == "oracle_quality":
        from oracle_telegram import oracle_quality_text, oracle_back_keyboard
        answer_callback(callback_id, "Oracle quality")
        edit_message(chat_id, message_id, oracle_quality_text(), reply_markup=oracle_back_keyboard())
        return
'''

text = text.replace(callback_insert_after, callback_oracle_block)

path.write_text(text, encoding="utf-8")

print("Patched telegram_bot.py successfully.")
print("Backup saved as telegram_bot_backup_before_oracle.py")