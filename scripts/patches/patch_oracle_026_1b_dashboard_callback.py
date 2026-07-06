from pathlib import Path

bot_file = Path("telegram_bot.py")

if not bot_file.exists():
    print("[ERROR] telegram_bot.py not found")
    raise SystemExit

text = bot_file.read_text(encoding="utf-8")

open_markers = [
    'if data == "oracle_dashboard":',
    "if data == 'oracle_dashboard':",
    'elif data == "oracle_dashboard":',
    "elif data == 'oracle_dashboard':",
    'if callback_data == "oracle_dashboard":',
    "if callback_data == 'oracle_dashboard':",
    'elif callback_data == "oracle_dashboard":',
    "elif callback_data == 'oracle_dashboard':",
]

patched = False

for marker in open_markers:
    if marker in text and "oracle_026_mark_dashboard_open(chat_id, message_id)" not in text:
        text = text.replace(
            marker,
            marker + "\n        oracle_026_mark_dashboard_open(chat_id, message_id)",
            1
        )
        print(f"[OK] Added dashboard open tracking near: {marker}")
        patched = True
        break

if not patched:
    print("[WARN] Could not find oracle_dashboard callback marker.")
    print("Send me the section around data == oracle_dashboard if this happens.")

bot_file.write_text(text, encoding="utf-8")
print("[DONE] ORACLE-026.1B patch applied")