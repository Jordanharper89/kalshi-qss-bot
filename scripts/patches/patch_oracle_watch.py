from pathlib import Path

path = Path("telegram_bot.py")
text = path.read_text(encoding="utf-8")

backup = Path("telegram_bot_backup_before_oracle_watch.py")
backup.write_text(text, encoding="utf-8")

insert_after = '''    if text == "/oracle_top":
        from oracle_telegram import oracle_top_text, oracle_back_keyboard
        send_message(chat_id, oracle_top_text(limit=10), reply_markup=oracle_back_keyboard())
        return
'''

insert_block = '''    if text == "/oracle_top":
        from oracle_telegram import oracle_top_text, oracle_back_keyboard
        send_message(chat_id, oracle_top_text(limit=10), reply_markup=oracle_back_keyboard())
        return

    if text == "/oracle_watch":
        from oracle_telegram import oracle_watch_text, oracle_back_keyboard
        send_message(chat_id, oracle_watch_text(limit=10), reply_markup=oracle_back_keyboard())
        return
'''

text = text.replace(insert_after, insert_block)

callback_after = '''    if data == "oracle_top":
        from oracle_telegram import oracle_top_text, oracle_back_keyboard
        answer_callback(callback_id, "Oracle top")
        edit_message(chat_id, message_id, oracle_top_text(limit=10), reply_markup=oracle_back_keyboard())
        return
'''

callback_block = '''    if data == "oracle_top":
        from oracle_telegram import oracle_top_text, oracle_back_keyboard
        answer_callback(callback_id, "Oracle top")
        edit_message(chat_id, message_id, oracle_top_text(limit=10), reply_markup=oracle_back_keyboard())
        return

    if data == "oracle_watch":
        from oracle_telegram import oracle_watch_text, oracle_back_keyboard
        answer_callback(callback_id, "Oracle watch")
        edit_message(chat_id, message_id, oracle_watch_text(limit=10), reply_markup=oracle_back_keyboard())
        return
'''

text = text.replace(callback_after, callback_block)

path.write_text(text, encoding="utf-8")

print("Patched Oracle watchlist into telegram_bot.py")
print("Backup saved as telegram_bot_backup_before_oracle_watch.py")