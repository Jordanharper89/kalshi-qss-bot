from pathlib import Path
from datetime import datetime

path = Path("oracle_continuous_intelligence.py")

if not path.exists():
    raise FileNotFoundError("oracle_continuous_intelligence.py not found.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

old = '''    # 1) Real market intelligence cards
    try:
        from oracle_market_intelligence import analyze_universe, get_top_intelligence

        analyze_universe(limit=500, top=50)
        cards = get_top_intelligence(limit=50)

        if isinstance(cards, list) and cards:
            return cards

    except Exception as e:
        print(f"[ORACLE-040.5] market intelligence source error: {e}")
'''

new = '''    # 1) Alpha Discovery cards — final Oracle research layer
    try:
        from oracle_alpha_discovery import run_alpha_discovery, get_top_alpha

        run_alpha_discovery(limit=50)
        cards = get_top_alpha(limit=50)

        if isinstance(cards, list) and cards:
            return cards

    except Exception as e:
        print(f"[ORACLE-044.4] alpha discovery source error: {e}")

    # 2) Final Fusion fallback
    try:
        from oracle_final_fusion import run_final_fusion, get_top_final

        run_final_fusion(limit=50)
        cards = get_top_final(limit=50)

        if isinstance(cards, list) and cards:
            return cards

    except Exception as e:
        print(f"[ORACLE-044.4] final fusion fallback error: {e}")

    # 3) Market Intelligence fallback
    try:
        from oracle_market_intelligence import analyze_universe, get_top_intelligence

        analyze_universe(limit=500, top=50)
        cards = get_top_intelligence(limit=50)

        if isinstance(cards, list) and cards:
            return cards

    except Exception as e:
        print(f"[ORACLE-044.4] market intelligence fallback error: {e}")
'''

if old not in text:
    raise RuntimeError("Could not find Market Intelligence source block in oracle_continuous_intelligence.py.")

text = text.replace(old, new)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE-044.4 INSTALLED")
print(" Continuous Pipeline now uses Alpha Discovery")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python oracle_continuous_intelligence.py")
print(" python telegram_bot.py")
print()
print("Telegram:")
print(" /oracle_intel")