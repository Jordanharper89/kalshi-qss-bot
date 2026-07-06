from pathlib import Path
from datetime import datetime

path = Path("telegram_bot.py")

if not path.exists():
    raise FileNotFoundError("telegram_bot.py not found. Run this from your bot folder.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

handler = '''
    if data == "oracle_run":
        answer_callback(callback_id, "Running research...", force=True)

        edit_message(
            chat_id,
            message_id,
            "🔮 ORACLE RESEARCH\\n\\nStatus:\\nRunning research cycle...",
            reply_markup=oracle_dashboard_back_keyboard(),
        )

        def finish_oracle_run():
            try:
                result = oracle_continuous_intelligence.run_cycle()
                output = f"""🔮 ORACLE RESEARCH COMPLETE

OK:
{result.get("ok")}

Opportunities Seen:
{result.get("opportunities_seen")}

Ranked:
{result.get("ranked")}

Events:
{result.get("events")}

High Priority Events:
{result.get("high_priority_events")}

Error:
{result.get("error")}
""".strip()
            except Exception as e:
                output = f"🔮 ORACLE RESEARCH ERROR\\n\\n{e}"

            edit_message(
                chat_id,
                message_id,
                output,
                reply_markup=oracle_dashboard_back_keyboard(),
            )

        run_background(finish_oracle_run)
        return

'''

if 'if data == "oracle_run":' not in text:
    marker = '''    if data == "oracle_dashboard":
'''
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find oracle_dashboard callback insertion point.")
    text = text[:idx] + handler + text[idx:]

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE RUN BUTTON FIXED")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python telegram_bot.py")
print()
print("Then hit Run Research.")