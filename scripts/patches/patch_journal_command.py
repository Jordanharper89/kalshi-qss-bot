from pathlib import Path

path = Path("telegram_bot.py")
text = path.read_text(encoding="utf-8")

backup = Path("telegram_bot_backup_before_journal.py")
backup.write_text(text, encoding="utf-8")

if "from journal_ui import journal_text, journal_keyboard" not in text:
    marker = "from services.service_manager import start_services, stop_services, service_diagnostics\n"
    text = text.replace(
        marker,
        marker + "from journal_ui import journal_text, journal_keyboard\n",
        1,
    )

insert_after = '''    if text == "/services":
        send_message(chat_id, service_diagnostics())
        return
'''

insert_block = '''    if text == "/services":
        send_message(chat_id, service_diagnostics())
        return

    if text == "/journal":
        send_message(chat_id, journal_text(limit=15), reply_markup=journal_keyboard())
        return
'''

text = text.replace(insert_after, insert_block, 1)

callback_after = '''    if data == "oracle_quality":
        from oracle_telegram import oracle_quality_text, oracle_back_keyboard
        answer_callback(callback_id, "Oracle quality")
        edit_message(chat_id, message_id, oracle_quality_text(), reply_markup=oracle_back_keyboard())
        return
'''

callback_block = '''    if data == "oracle_quality":
        from oracle_telegram import oracle_quality_text, oracle_back_keyboard
        answer_callback(callback_id, "Oracle quality")
        edit_message(chat_id, message_id, oracle_quality_text(), reply_markup=oracle_back_keyboard())
        return

    if data == "journal":
        answer_callback(callback_id, "Journal")
        edit_message(chat_id, message_id, journal_text(limit=15), reply_markup=journal_keyboard())
        return
'''

text = text.replace(callback_after, callback_block, 1)

path.write_text(text, encoding="utf-8")

print("Patched /journal command.")
print("Backup saved as telegram_bot_backup_before_journal.py")