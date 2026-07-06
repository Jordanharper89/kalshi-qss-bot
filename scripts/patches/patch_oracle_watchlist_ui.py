from pathlib import Path

path = Path("telegram_bot.py")
text = path.read_text(encoding="utf-8")

backup = Path("telegram_bot_backup_before_oracle_watchlist_ui.py")
backup.write_text(text, encoding="utf-8")

if "from oracle_watchlist_ui import oracle_watchlist_text, oracle_watchlist_keyboard, oracle_watch_added_text" not in text:
    marker = "from notification_ui import notification_text, notification_keyboard\n"
    text = text.replace(
        marker,
        marker + "from oracle_watchlist_ui import oracle_watchlist_text, oracle_watchlist_keyboard, oracle_watch_added_text\n",
        1,
    )

cmd_marker = '''    if text == "/notifications":
        send_message(chat_id, notification_text(), reply_markup=notification_keyboard())
        return
'''

cmd_replace = '''    if text == "/notifications":
        send_message(chat_id, notification_text(), reply_markup=notification_keyboard())
        return

    if text == "/oracle_watchlist":
        send_message(chat_id, oracle_watchlist_text(), reply_markup=oracle_watchlist_keyboard())
        return
'''

text = text.replace(cmd_marker, cmd_replace, 1)

callback_marker = '''    if data == "notifications_flush":
        answer_callback(callback_id, "Flushing")
        notification_service.flush_all(limit=25)
        edit_message(chat_id, message_id, notification_text(), reply_markup=notification_keyboard())
        return
'''

callback_replace = '''    if data == "notifications_flush":
        answer_callback(callback_id, "Flushing")
        notification_service.flush_all(limit=25)
        edit_message(chat_id, message_id, notification_text(), reply_markup=notification_keyboard())
        return

    if data == "oracle_watchlist":
        answer_callback(callback_id, "Oracle watchlist")
        edit_message(chat_id, message_id, oracle_watchlist_text(), reply_markup=oracle_watchlist_keyboard())
        return

    if data.startswith("oracle_watch_ticker|"):
        ticker = data.split("|", 1)[1]
        answer_callback(callback_id, "Watching")
        edit_message(chat_id, message_id, oracle_watch_added_text(ticker), reply_markup=oracle_watchlist_keyboard())
        return
'''

text = text.replace(callback_marker, callback_replace, 1)

path.write_text(text, encoding="utf-8")

print("Patched Oracle watchlist UI.")
print("Backup saved as telegram_bot_backup_before_oracle_watchlist_ui.py")