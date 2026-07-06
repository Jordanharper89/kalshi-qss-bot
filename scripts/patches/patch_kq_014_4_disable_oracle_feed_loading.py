from pathlib import Path

bot_file = Path("telegram_bot.py")

if not bot_file.exists():
    print("[ERROR] telegram_bot.py not found")
    raise SystemExit

text = bot_file.read_text(encoding="utf-8")

backup = Path("telegram_bot.py.kq0144_backup")
backup.write_text(text, encoding="utf-8")
print("[OK] Backup saved:", backup)

replacements = [
    ("Oracle feed loading", "[KQ-014.4 skipped Oracle feed loading]"),
    ("Loading Oracle feed", "[KQ-014.4 skipped Oracle feed loading]"),
    ("Loading oracle feed", "[KQ-014.4 skipped Oracle feed loading]"),
    ("Refreshing Oracle feed", "[KQ-014.4 skipped Oracle feed loading]"),
    ("Oracle Feed loading", "[KQ-014.4 skipped Oracle feed loading]"),
]

changed = False

for old, new in replacements:
    if old in text:
        text = text.replace(old, new)
        print(f"[OK] Replaced loading text: {old}")
        changed = True

bot_file.write_text(text, encoding="utf-8")

if changed:
    print("[DONE] KQ-014.4 patch applied")
else:
    print("[WARN] No loading text found. Need exact oracle_feed code block next.")