from pathlib import Path

bot_file = Path("telegram_bot.py")

if not bot_file.exists():
    print("[ERROR] telegram_bot.py not found")
    raise SystemExit

text = bot_file.read_text(encoding="utf-8")

backup = Path("telegram_bot.py.kq0145_backup")
backup.write_text(text, encoding="utf-8")
print("[OK] Backup saved:", backup)

old = '''def edit_oracle_feed_fast(chat_id, message_id):
    edit_message(
        chat_id,
        message_id,
        "ORACLE OPPORTUNITY FEED\\n\\nStatus:\\nRefreshing Top 10 live edges...",
        reply_markup=oracle_feed_keyboard(),
    )

    def finish_oracle_feed():'''

new = '''def edit_oracle_feed_fast(chat_id, message_id):
    # KQ-014.5:
    # Removed instant placeholder edit to prevent duplicate Telegram edits.
    # The background worker now sends only the final Oracle Feed message.

    def finish_oracle_feed():'''

if old not in text:
    print("[ERROR] Exact Oracle Feed placeholder block not found.")
    print("No changes made.")
    raise SystemExit

text = text.replace(old, new, 1)
bot_file.write_text(text, encoding="utf-8")

print("[DONE] KQ-014.5 removed Oracle Feed placeholder edit")