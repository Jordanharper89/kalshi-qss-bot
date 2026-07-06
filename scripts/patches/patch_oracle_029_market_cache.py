from pathlib import Path

root = Path.cwd()

cache_file = root / "oracle_market_cache.py"
bot_file = root / "telegram_bot.py"

cache_code = r'''
"""
ORACLE-029 — Shared Market Cache
"""

import threading
import time


class OracleMarketCache:

    def __init__(self):
        self.lock = threading.Lock()
        self.markets = {}
        self.last_refresh = None

    def update_market(self, ticker, data):
        with self.lock:
            self.markets[ticker] = data
            self.last_refresh = time.time()

    def get_market(self, ticker):
        with self.lock:
            return self.markets.get(ticker)

    def get_all(self):
        with self.lock:
            return dict(self.markets)

    def market_count(self):
        with self.lock:
            return len(self.markets)

    def diagnostics(self):
        return {
            "markets": self.market_count(),
            "last_refresh": self.last_refresh,
        }


oracle_market_cache = OracleMarketCache()
'''

cache_file.write_text(cache_code, encoding="utf-8")
print("[OK] oracle_market_cache.py created")

if bot_file.exists():

    text = bot_file.read_text(encoding="utf-8")

    if "from oracle_market_cache import oracle_market_cache" not in text:
        text = (
            "from oracle_market_cache import oracle_market_cache\n"
            + text
        )
        print("[OK] Added market cache import")

    bot_file.write_text(text, encoding="utf-8")

print("[DONE] ORACLE-029 installed")