"""
Fix Oracle Back Keyboard Name Conflict

Problem:
telegram_bot.py already imports/uses oracle_back_keyboard from oracle_telegram
inside some callback branches. That makes Python treat oracle_back_keyboard
as a local variable inside _handle_callback_inner(), causing UnboundLocalError
when our new dashboard branches call oracle_back_keyboard().

Fix:
Rename the new helper to oracle_dashboard_back_keyboard().
"""

from pathlib import Path
from datetime import datetime

BOT_FILE = Path("telegram_bot.py")

text = BOT_FILE.read_text(encoding="utf-8")

backup = Path(
    f"telegram_bot_backup_before_oracle_back_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
)
backup.write_text(text, encoding="utf-8")

text = text.replace(
    "def oracle_back_keyboard():",
    "def oracle_dashboard_back_keyboard():",
)

text = text.replace(
    "reply_markup=oracle_back_keyboard())",
    "reply_markup=oracle_dashboard_back_keyboard())",
)

text = text.replace(
    "return text, oracle_back_keyboard()",
    "return text, oracle_dashboard_back_keyboard()",
)

BOT_FILE.write_text(text, encoding="utf-8")

print("Oracle back keyboard fix applied.")
print(f"Backup created: {backup}")