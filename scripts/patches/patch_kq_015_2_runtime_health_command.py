from pathlib import Path
from datetime import datetime

path = Path("telegram_bot.py")

if not path.exists():
    raise FileNotFoundError("telegram_bot.py not found. Run this from your bot folder.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

helper = r'''

def runtime_health_text():
    """
    KQ-015.2:
    Runtime health report for Telegram.
    """
    lines = []
    lines.append("🧪 KQ / ORACLE RUNTIME HEALTH")
    lines.append("")

    try:
        lines.append("Telegram Queue:")
        lines.append(f"Pending: {telegram_queue_size()}")
        lines.append("")
    except Exception as e:
        lines.append(f"Telegram Queue Error: {e}")
        lines.append("")

    try:
        import oracle_message_cache
        lines.append("Message Cache:")
        lines.append(str(oracle_message_cache.diagnostics()))
        lines.append("")
    except Exception as e:
        lines.append(f"Message Cache Error: {e}")
        lines.append("")

    try:
        lines.append("Continuous Intelligence:")
        lines.append(oracle_continuous_intelligence.format_status())
        lines.append("")
    except Exception as e:
        lines.append(f"Continuous Intelligence Error: {e}")
        lines.append("")

    try:
        from oracle_market_memory import format_memory_summary
        lines.append("Market Memory:")
        lines.append(format_memory_summary())
        lines.append("")
    except Exception as e:
        lines.append(f"Market Memory Error: {e}")
        lines.append("")

    try:
        lines.append("Services:")
        lines.append(service_diagnostics())
    except Exception as e:
        lines.append(f"Service Diagnostics Error: {e}")

    return "\\n".join(lines).strip()

'''

if "def runtime_health_text():" not in text:
    marker = "\ndef handle_waiting_input(chat_id, text):"
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find insertion point before handle_waiting_input.")
    text = text[:idx] + helper + text[idx:]

# Add help text
if "/health = Runtime health check" not in text:
    text = text.replace(
        "/help = Help\n",
        "/help = Help\n/health = Runtime health check\n",
    )

# Add command handler
command_block = '''
    if text == "/health":
        send_message(chat_id, runtime_health_text(), reply_markup=main_menu_keyboard())
        return

'''

if 'if text == "/health":' not in text:
    marker = '''    if text == "/services":
'''
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find /services command insertion point.")
    text = text[:idx] + command_block + text[idx:]

path.write_text(text, encoding="utf-8")

print("===================================")
print(" KQ-015.2 INSTALLED")
print(" Runtime Health Command")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python telegram_bot.py")
print()
print("Telegram:")
print(" /health")