from pathlib import Path

bot_file = Path("telegram_bot.py")

if not bot_file.exists():
    print("[ERROR] telegram_bot.py not found")
    raise SystemExit

text = bot_file.read_text(encoding="utf-8")

backup = Path("telegram_bot.py.kq0143_backup")
backup.write_text(text, encoding="utf-8")
print("[OK] Backup saved:", backup)

old_patterns = [
    'telegram_queue_request("editMessageText",',
    "telegram_queue_request('editMessageText',",
]

lines = text.splitlines()
new_lines = []

inside_oracle_feed = False
skipped_one = False

for line in lines:
    stripped = line.strip()

    if 'data == "oracle_feed"' in line or "data == 'oracle_feed'" in line:
        inside_oracle_feed = True
        skipped_one = False
        new_lines.append(line)
        continue

    if inside_oracle_feed:
        if "finish_oracle_feed" in line:
            inside_oracle_feed = False
            new_lines.append(line)
            continue

        if not skipped_one and any(p in line for p in old_patterns):
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(indent + "# KQ-014.3 skipped instant Oracle Feed placeholder edit")
            skipped_one = True
            print("[OK] Removed duplicate Oracle Feed placeholder edit")
            continue

    new_lines.append(line)

patched = "\n".join(new_lines)

if patched == text:
    print("[WARN] No oracle_feed placeholder edit found.")
    print("This patch did not change telegram_bot.py.")
else:
    bot_file.write_text(patched, encoding="utf-8")
    print("[DONE] KQ-014.3 patch applied")