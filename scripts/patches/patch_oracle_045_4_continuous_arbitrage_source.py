from pathlib import Path
from datetime import datetime

path = Path("oracle_continuous_intelligence.py")

if not path.exists():
    raise FileNotFoundError("oracle_continuous_intelligence.py not found.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

old = '''    # 1) Alpha Discovery cards — final Oracle research layer
    try:
        from oracle_alpha_discovery import run_alpha_discovery, get_top_alpha

        run_alpha_discovery(limit=50)
        cards = get_top_alpha(limit=50)

        if isinstance(cards, list) and cards:
            return cards

    except Exception as e:
        print(f"[ORACLE-044.4] alpha discovery source error: {e}")
'''

new = '''    # 1) Arbitrage alerts — highest priority inefficiency source
    try:
        from oracle_cross_market_arbitrage import run_arbitrage_scan, get_top_arbitrage

        run_arbitrage_scan()
        arb = get_top_arbitrage(limit=20)

        if isinstance(arb, list) and arb:
            converted = []
            for item in arb:
                converted.append({
                    "ticker": "ARBITRAGE-" + str(item.get("kind", "UNKNOWN")).upper(),
                    "title": item.get("title") or "Cross-market arbitrage alert",
                    "side": "WATCH",
                    "edge": item.get("edge"),
                    "confidence": item.get("confidence"),
                    "fair_value": 0,
                    "market_price": 0,
                    "volume": 0,
                    "age_seconds": 0,
                    "providers": ["oracle_arbitrage", "kalshi_universe"],
                    "recommendation": item.get("recommendation"),
                    "reason": item.get("reason"),
                    "raw": item,
                })

            return converted

    except Exception as e:
        print(f"[ORACLE-045.4] arbitrage source error: {e}")

    # 2) Alpha Discovery cards — final Oracle research layer
    try:
        from oracle_alpha_discovery import run_alpha_discovery, get_top_alpha

        run_alpha_discovery(limit=50)
        cards = get_top_alpha(limit=50)

        if isinstance(cards, list) and cards:
            return cards

    except Exception as e:
        print(f"[ORACLE-045.4] alpha discovery fallback error: {e}")
'''

if old not in text:
    raise RuntimeError("Could not find Alpha Discovery source block.")

text = text.replace(old, new)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE-045.4 INSTALLED")
print(" Continuous Pipeline now checks Arbitrage first")
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