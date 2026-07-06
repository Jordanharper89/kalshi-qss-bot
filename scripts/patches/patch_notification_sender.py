from pathlib import Path

path = Path("telegram_bot.py")
text = path.read_text(encoding="utf-8")

backup = Path("telegram_bot_backup_before_notification_sender.py")
backup.write_text(text, encoding="utf-8")

import_line = "from services.service_manager import start_services, stop_services, service_diagnostics\n"

if "from services.notification_service import notification_service\n" not in text:
    text = text.replace(
        import_line,
        import_line + "from services.notification_service import notification_service\n",
        1,
    )

old = """    start_services()

    start_telegram_queue(BASE, diag_fn=diag)
"""

new = """    start_services()
    notification_service.configure_sender(send_message, CHAT_ID)

    start_telegram_queue(BASE, diag_fn=diag)
"""

text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")

print("Patched notification sender into telegram_bot.py")
print("Backup saved as telegram_bot_backup_before_notification_sender.py")