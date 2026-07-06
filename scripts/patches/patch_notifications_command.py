from pathlib import Path

path = Path("telegram_bot.py")
text = path.read_text(encoding="utf-8")

backup = Path("telegram_bot_backup_before_notifications.py")
backup.write_text(text, encoding="utf-8")

service_import = "from services.notification_service import notification_service\n"

if "from notification_ui import notification_text, notification_keyboard\n" not in text:
    text = text.replace(
        service_import,
        service_import + "from notification_ui import notification_text, notification_keyboard\n",
        1,
    )

old_cmd = '''    if text == "/journal":
        send_message(chat_id, journal_text(limit=15), reply_markup=journal_keyboard())
        return
'''

new_cmd = '''    if text == "/journal":
        send_message(chat_id, journal_text(limit=15), reply_markup=journal_keyboard())
        return

    if text == "/notifications":
        send_message(chat_id, notification_text(), reply_markup=notification_keyboard())
        return
'''

text = text.replace(old_cmd, new_cmd, 1)

old_callback = '''    if data == "journal":
        answer_callback(callback_id, "Journal")
        edit_message(chat_id, message_id, journal_text(limit=15), reply_markup=journal_keyboard())
        return
'''

new_callback = '''    if data == "journal":
        answer_callback(callback_id, "Journal")
        edit_message(chat_id, message_id, journal_text(limit=15), reply_markup=journal_keyboard())
        return

    if data == "notifications":
        answer_callback(callback_id, "Notifications")
        edit_message(chat_id, message_id, notification_text(), reply_markup=notification_keyboard())
        return

    if data == "notifications_flush":
        answer_callback(callback_id, "Flushing")
        notification_service.flush_all(limit=25)
        edit_message(chat_id, message_id, notification_text(), reply_markup=notification_keyboard())
        return
'''

text = text.replace(old_callback, new_callback, 1)

path.write_text(text, encoding="utf-8")

print("Patched /notifications command.")
print("Backup saved as telegram_bot_backup_before_notifications.py")