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

def startup_health_check():
    """
    KQ-015.1:
    Simple startup health check for critical Oracle/KQ modules.
    Prints OK/MISSING before bot begins polling.
    """
    checks = [
        ("oracle_message_cache", "should_skip_dashboard_edit"),
        ("oracle_dashboard_refresh", "start_dashboard_refresh"),
        ("oracle_continuous_intelligence", "start"),
        ("oracle_event_alert_ui", "recent_event_alerts_text"),
        ("oracle_event_pipeline", "process_opportunities"),
        ("oracle_market_memory", "memory_summary"),
        ("oracle_self_learning", "recommend_multiplier"),
        ("oracle_adaptive_ranking", "rank_opportunities"),
    ]

    print("")
    print("KQ-015.1 STARTUP HEALTH CHECK")
    print("-----------------------------------")

    ok_count = 0
    fail_count = 0

    for module_name, attr_name in checks:
        try:
            module = importlib.import_module(module_name)
            getattr(module, attr_name)
            print(f"OK      {module_name}.{attr_name}")
            ok_count += 1
        except Exception as e:
            print(f"MISSING {module_name}.{attr_name} -> {e}")
            fail_count += 1

    print("-----------------------------------")
    print(f"Startup Health: {ok_count} OK / {fail_count} issues")
    print("")

    return fail_count == 0

'''

if "def startup_health_check():" not in text:
    marker = "\ndef main():\n"
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Could not find main() insertion point.")
    text = text[:idx] + helper + text[idx:]

startup_call = '''    startup_health_check()
'''

if startup_call not in text:
    marker = '''    print("KQ-010.1 fast Telegram UI + diagnostics active. Watch CMD for callback timing.")
'''
    if marker not in text:
        raise RuntimeError("Could not find startup print insertion point.")
    text = text.replace(marker, marker + "\n" + startup_call)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" KQ-015.1 INSTALLED")
print(" Startup Health Check")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python telegram_bot.py")
print()
print("Expected:")
print(" KQ-015.1 STARTUP HEALTH CHECK")
print(" OK oracle_message_cache.should_skip_dashboard_edit")