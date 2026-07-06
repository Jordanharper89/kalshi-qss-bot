
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




# ============================================================
# ORACLE V2.0 Live Data Layer Cache Bridge
# ============================================================

try:
    from oracle_v2_live_data_layer import oracle_v2_live_data_layer
except Exception:
    oracle_v2_live_data_layer = None


def _oracle_v2_cache_snapshot():
    if oracle_v2_live_data_layer is None:
        return {"markets": 0, "last_refresh": None, "status": "missing_v2_layer"}

    snap = oracle_v2_live_data_layer.refresh()
    return {
        "markets": snap.get("markets", 0),
        "last_refresh": snap.get("last_refresh"),
        "status": "ok",
        "source": "oracle_v2_live_data_layer",
    }


def diagnostics():
    try:
        return _oracle_v2_cache_snapshot()
    except Exception as exc:
        return {"markets": 0, "last_refresh": None, "status": "error", "error": str(exc)}


def get_markets():
    try:
        if oracle_v2_live_data_layer is None:
            return []
        return oracle_v2_live_data_layer.get_markets()
    except Exception:
        return []


# If old singleton exists, attach V2 methods to it too.
try:
    if "oracle_market_cache" in globals():
        oracle_market_cache.diagnostics = diagnostics
        oracle_market_cache.get_markets = get_markets
except Exception:
    pass

# ============================================================
# END ORACLE V2.0
# ============================================================

