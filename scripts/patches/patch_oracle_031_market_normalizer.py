from pathlib import Path

root = Path.cwd()

normalizer_file = root / "oracle_market_normalizer.py"
engine_file = root / "oracle_research_engine.py"

normalizer_file.write_text(r'''
"""
ORACLE-031 — Market Normalization Engine

Purpose:
- Convert provider-specific market dictionaries into one standard Oracle format.
- All downstream systems should read normalized fields only.
"""

import time


def _num(value, default=0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def normalize_market(market, provider="unknown"):
    """
    Standard Oracle market schema.
    Accepts flexible provider fields and converts them into consistent names.
    """

    ticker = (
        market.get("ticker")
        or market.get("market_ticker")
        or market.get("id")
        or market.get("symbol")
    )

    title = (
        market.get("title")
        or market.get("name")
        or market.get("question")
        or ticker
        or "Untitled Market"
    )

    yes_price = _num(
        market.get("yes_price")
        or market.get("yes")
        or market.get("yes_bid")
        or market.get("last_price")
        or market.get("price")
    )

    no_price = _num(
        market.get("no_price")
        or market.get("no")
        or market.get("no_bid")
        or (100 - yes_price if yes_price else 0)
    )

    volume = _num(
        market.get("volume")
        or market.get("volume_24h")
        or market.get("total_volume")
    )

    liquidity = _num(
        market.get("liquidity")
        or market.get("open_interest")
        or market.get("depth")
    )

    expiration = (
        market.get("expiration")
        or market.get("close_time")
        or market.get("expiration_time")
        or market.get("end_date")
    )

    return {
        "ticker": ticker,
        "title": title,
        "yes_price": yes_price,
        "no_price": no_price,
        "volume": volume,
        "liquidity": liquidity,
        "expiration": expiration,
        "provider": provider,
        "raw_provider": market.get("provider", provider),
        "normalized_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "raw": market,
    }
''', encoding="utf-8")

print("[OK] Created oracle_market_normalizer.py")

if not engine_file.exists():
    print("[ERROR] oracle_research_engine.py not found")
    raise SystemExit

text = engine_file.read_text(encoding="utf-8")

backup = root / "oracle_research_engine.py.oracle031_backup"
backup.write_text(text, encoding="utf-8")
print("[OK] Backup saved:", backup)

if "from oracle_market_normalizer import normalize_market" not in text:
    text = "from oracle_market_normalizer import normalize_market\n" + text
    print("[OK] Added normalizer import")

old = '''                market["provider"] = provider_name
                market["cached_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                oracle_market_cache.update_market(ticker, market)
                markets_checked += 1
'''

new = '''                normalized = normalize_market(market, provider_name)
                normalized["cached_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

                normalized_ticker = normalized.get("ticker")
                if not normalized_ticker:
                    continue

                oracle_market_cache.update_market(normalized_ticker, normalized)
                markets_checked += 1
'''

if old not in text:
    print("[ERROR] Could not find market cache update block.")
    print("No changes made to oracle_research_engine.py.")
    raise SystemExit

text = text.replace(old, new, 1)
engine_file.write_text(text, encoding="utf-8")

print("[DONE] ORACLE-031 market normalizer installed")