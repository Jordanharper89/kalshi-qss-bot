from pathlib import Path

path = Path("telegram_bot.py")
text = path.read_text(encoding="utf-8")

backup = Path("telegram_bot_backup_before_services.py")
backup.write_text(text, encoding="utf-8")

if "from services.service_manager import start_services, stop_services, service_diagnostics" not in text:
    marker = "import requests\n"
    text = text.replace(
        marker,
        marker + "from services.service_manager import start_services, stop_services, service_diagnostics\n",
        1,
    )

old = '''    start_telegram_queue(BASE, diag_fn=diag)
    start_position_monitor(send_message_fn=send_message, chat_id=CHAT_ID)
'''

new = '''    start_services()

    start_telegram_queue(BASE, diag_fn=diag)
    start_position_monitor(send_message_fn=send_message, chat_id=CHAT_ID)
'''

text = text.replace(old, new, 1)

old_cmd = '''    if text == "/queue":
        send_message(chat_id, f"TELEGRAM QUEUE\\n\\nPending requests:\\n{telegram_queue_size()}")
        return
'''

new_cmd = '''    if text == "/services":
        send_message(chat_id, service_diagnostics())
        return

    if text == "/queue":
        send_message(chat_id, f"TELEGRAM QUEUE\\n\\nPending requests:\\n{telegram_queue_size()}")
        return
'''

text = text.replace(old_cmd, new_cmd, 1)

path.write_text(text, encoding="utf-8")

print("Patched telegram_bot.py with service startup.")
print("Backup saved as telegram_bot_backup_before_services.py")