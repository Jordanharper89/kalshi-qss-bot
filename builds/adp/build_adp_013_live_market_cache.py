from pathlib import Path

ROOT = Path("qseries_v2")
ADAPTERS = ROOT / "adapters"
ADAPTERS.mkdir(parents=True, exist_ok=True)

cache_code = r'''"""
ADP-013 — Live Market Cache & Synchronization Engine

Purpose:
- Cache normalized Kalshi markets from ADP-012.
- Provide one shared market source for Oracle, Q Series, Telegram, and future scanners.
- Support manual refresh and optional background sync.
- Read-only only. No trade execution.
"""

import time
import threading
from typing import Any, Dict, List, Optional


class LiveMarketCacheError(Exception):
    pass


class LiveKalshiMarketCache:
    def __init__(
        self,
        ingestion: Any,
        event_bus: Any = None,
        refresh_interval_seconds: float = 30.0,
    ):
        if ingestion is None:
            raise LiveMarketCacheError("ADP-013 requires an ADP-012 ingestion object.")

        self.ingestion = ingestion
        self.event_bus = event_bus
        self.refresh_interval_seconds = float(refresh_interval_seconds)

        self._lock = threading.RLock()
        self._markets_by_ticker: Dict[str, Dict[str, Any]] = {}
        self._markets_by_event: Dict[str, List[str]] = {}
        self._markets_by_series: Dict[str, List[str]] = {}
        self._markets_by_category: Dict[str, List[str]] = {}

        self._refresh_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        self.refresh_count = 0
        self.error_count = 0
        self.last_error: Optional[str] = None
        self.last_refresh_started_at: Optional[float] = None
        self.last_refresh_finished_at: Optional[float] = None
        self.last_refresh_duration_seconds: Optional[float] = None
        self.last_refresh_summary: Dict[str, Any] = {
            "status": "empty",
            "added": 0,
            "changed": 0,
            "removed": 0,
            "unchanged": 0,
            "count": 0,
        }

    def _emit(self, event_type: str, payload: Dict[str, Any]):
        if self.event_bus is None:
            return

        try:
            if hasattr(self.event_bus, "publish"):
                self.event_bus.publish(event_type, payload)
            elif hasattr(self.event_bus, "emit"):
                self.event_bus.emit(event_type, payload)
        except Exception:
            pass

    def _index(self):
        self._markets_by_event = {}
        self._markets_by_series = {}
        self._markets_by_category = {}

        for ticker, market in self._markets_by_ticker.items():
            event_ticker = market.get("event_ticker")
            if event_ticker:
                self._markets_by_event.setdefault(event_ticker, []).append(ticker)

            series_ticker = market.get("series_ticker") or self._infer_series_ticker(ticker)
            if series_ticker:
                self._markets_by_series.setdefault(series_ticker, []).append(ticker)

            category = market.get("category")
            if category:
                self._markets_by_category.setdefault(category, []).append(ticker)

    def _infer_series_ticker(self, ticker: str) -> Optional[str]:
        if not ticker or "-" not in ticker:
            return None
        return ticker.split("-")[0]

    def _market_changed(self, old: Dict[str, Any], new: Dict[str, Any]) -> bool:
        watched_fields = [
            "yes_bid",
            "yes_ask",
            "no_bid",
            "no_ask",
            "last_price",
            "volume",
            "open_interest",
            "liquidity",
            "status",
            "close_time",
            "expiration_time",
            "title",
            "subtitle",
        ]

        for field in watched_fields:
            if old.get(field) != new.get(field):
                return True

        return False

    def refresh(
        self,
        status: str = "open",
        limit: int = 1000,
        max_pages: int = 3,
    ) -> Dict[str, Any]:
        started = time.time()

        with self._lock:
            self.last_refresh_started_at = started

        try:
            all_markets: List[Dict[str, Any]] = []
            cursor = None
            page_count = 0

            while page_count < max_pages:
                snapshot = self.ingestion.fetch_markets(
                    status=status,
                    limit=limit,
                    cursor=cursor,
                )

                if snapshot.get("status") != "ok":
                    raise LiveMarketCacheError(snapshot.get("error") or "ADP-012 refresh failed.")

                markets = snapshot.get("markets", [])
                all_markets.extend(markets)

                cursor = snapshot.get("cursor")
                page_count += 1

                if not cursor:
                    break

            incoming_by_ticker = {
                market.get("ticker"): market
                for market in all_markets
                if market.get("ticker")
            }

            with self._lock:
                old_tickers = set(self._markets_by_ticker.keys())
                new_tickers = set(incoming_by_ticker.keys())

                added_tickers = sorted(list(new_tickers - old_tickers))
                removed_tickers = sorted(list(old_tickers - new_tickers))

                changed_tickers = []
                unchanged = 0

                for ticker in sorted(list(new_tickers & old_tickers)):
                    if self._market_changed(self._markets_by_ticker[ticker], incoming_by_ticker[ticker]):
                        changed_tickers.append(ticker)
                    else:
                        unchanged += 1

                self._markets_by_ticker = incoming_by_ticker
                self._index()

                finished = time.time()
                self.last_refresh_finished_at = finished
                self.last_refresh_duration_seconds = finished - started
                self.refresh_count += 1
                self.last_error = None

                summary = {
                    "module": "adp_013_live_market_cache",
                    "status": "ok",
                    "market_status_filter": status,
                    "count": len(self._markets_by_ticker),
                    "added": len(added_tickers),
                    "changed": len(changed_tickers),
                    "removed": len(removed_tickers),
                    "unchanged": unchanged,
                    "added_tickers": added_tickers[:25],
                    "changed_tickers": changed_tickers[:25],
                    "removed_tickers": removed_tickers[:25],
                    "page_count": page_count,
                    "has_more": bool(cursor),
                    "duration_seconds": round(self.last_refresh_duration_seconds, 4),
                    "timestamp": finished,
                }

                self.last_refresh_summary = summary

            self._emit("adp.market.cache.updated", summary)

            for ticker in added_tickers[:50]:
                self._emit("adp.market.created", {"ticker": ticker, "timestamp": time.time()})

            for ticker in changed_tickers[:50]:
                self._emit("adp.market.changed", {"ticker": ticker, "timestamp": time.time()})

            for ticker in removed_tickers[:50]:
                self._emit("adp.market.removed", {"ticker": ticker, "timestamp": time.time()})

            return summary

        except Exception as exc:
            with self._lock:
                self.error_count += 1
                self.last_error = str(exc)
                self.last_refresh_finished_at = time.time()
                self.last_refresh_duration_seconds = self.last_refresh_finished_at - started
                self.last_refresh_summary = {
                    "module": "adp_013_live_market_cache",
                    "status": "error",
                    "error": str(exc),
                    "count": len(self._markets_by_ticker),
                    "duration_seconds": round(self.last_refresh_duration_seconds, 4),
                    "timestamp": self.last_refresh_finished_at,
                }

            self._emit("adp.market.cache.error", self.last_refresh_summary)
            return self.last_refresh_summary

    def start(self):
        if self._refresh_thread and self._refresh_thread.is_alive():
            return {"status": "already_running", "interval": self.refresh_interval_seconds}

        self._stop_event.clear()

        def loop():
            while not self._stop_event.is_set():
                self.refresh()
                self._stop_event.wait(self.refresh_interval_seconds)

        self._refresh_thread = threading.Thread(target=loop, daemon=True)
        self._refresh_thread.start()

        return {"status": "started", "interval": self.refresh_interval_seconds}

    def stop(self):
        self._stop_event.set()
        return {"status": "stopping"}

    def get_market(self, ticker: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            market = self._markets_by_ticker.get(ticker)
            return dict(market) if market else None

    def get_all_markets(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [dict(m) for m in self._markets_by_ticker.values()]

    def get_open_markets(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                dict(m)
                for m in self._markets_by_ticker.values()
                if (m.get("status") or "").lower() == "open"
            ]

    def get_event(self, event_ticker: str) -> List[Dict[str, Any]]:
        with self._lock:
            tickers = self._markets_by_event.get(event_ticker, [])
            return [dict(self._markets_by_ticker[t]) for t in tickers if t in self._markets_by_ticker]

    def get_series(self, series_ticker: str) -> List[Dict[str, Any]]:
        with self._lock:
            tickers = self._markets_by_series.get(series_ticker, [])
            return [dict(self._markets_by_ticker[t]) for t in tickers if t in self._markets_by_ticker]

    def get_category(self, category: str) -> List[Dict[str, Any]]:
        with self._lock:
            tickers = self._markets_by_category.get(category, [])
            return [dict(self._markets_by_ticker[t]) for t in tickers if t in self._markets_by_ticker]

    def statistics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "module": "adp_013_live_market_cache",
                "status": "ok" if not self.last_error else "error",
                "market_count": len(self._markets_by_ticker),
                "event_count": len(self._markets_by_event),
                "series_count": len(self._markets_by_series),
                "category_count": len(self._markets_by_category),
                "refresh_count": self.refresh_count,
                "error_count": self.error_count,
                "last_error": self.last_error,
                "last_refresh_started_at": self.last_refresh_started_at,
                "last_refresh_finished_at": self.last_refresh_finished_at,
                "last_refresh_duration_seconds": self.last_refresh_duration_seconds,
                "last_refresh_summary": dict(self.last_refresh_summary),
                "background_running": bool(self._refresh_thread and self._refresh_thread.is_alive()),
                "refresh_interval_seconds": self.refresh_interval_seconds,
                "read_only": True,
            }

    def diagnostics(self) -> Dict[str, Any]:
        return self.statistics()


def build_live_market_cache(
    ingestion: Any,
    event_bus: Any = None,
    refresh_interval_seconds: float = 30.0,
) -> LiveKalshiMarketCache:
    return LiveKalshiMarketCache(
        ingestion=ingestion,
        event_bus=event_bus,
        refresh_interval_seconds=refresh_interval_seconds,
    )


if __name__ == "__main__":
    from qseries_v2.adapters.live_kalshi_market_ingestion import build_live_kalshi_market_ingestion

    ingestion = build_live_kalshi_market_ingestion(environment="production")
    cache = build_live_market_cache(ingestion=ingestion)
    print(cache.diagnostics())
    print(cache.refresh(limit=25, max_pages=1))
    print(cache.statistics())
'''

test_code = r'''"""
Test ADP-013 Live Market Cache without hitting Kalshi.
"""

from qseries_v2.adapters.live_market_cache import LiveKalshiMarketCache


class FakeIngestion:
    def __init__(self):
        self.call_count = 0

    def fetch_markets(self, status="open", limit=1000, cursor=None):
        self.call_count += 1

        if self.call_count == 1:
            return {
                "status": "ok",
                "cursor": None,
                "markets": [
                    {
                        "ticker": "SERIES-EVENT-001",
                        "event_ticker": "EVENT",
                        "series_ticker": "SERIES",
                        "category": "Test",
                        "title": "Market 1",
                        "yes_bid": 40,
                        "yes_ask": 42,
                        "status": "open",
                    },
                    {
                        "ticker": "SERIES-EVENT-002",
                        "event_ticker": "EVENT",
                        "series_ticker": "SERIES",
                        "category": "Test",
                        "title": "Market 2",
                        "yes_bid": 50,
                        "yes_ask": 52,
                        "status": "open",
                    },
                ],
            }

        return {
            "status": "ok",
            "cursor": None,
            "markets": [
                {
                    "ticker": "SERIES-EVENT-001",
                    "event_ticker": "EVENT",
                    "series_ticker": "SERIES",
                    "category": "Test",
                    "title": "Market 1",
                    "yes_bid": 41,
                    "yes_ask": 43,
                    "status": "open",
                },
                {
                    "ticker": "SERIES-EVENT-003",
                    "event_ticker": "EVENT2",
                    "series_ticker": "SERIES",
                    "category": "Other",
                    "title": "Market 3",
                    "yes_bid": 60,
                    "yes_ask": 62,
                    "status": "open",
                },
            ],
        }


class FakeEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event_type, payload):
        self.events.append((event_type, payload))


def test_adp_013():
    ingestion = FakeIngestion()
    bus = FakeEventBus()
    cache = LiveKalshiMarketCache(ingestion=ingestion, event_bus=bus, refresh_interval_seconds=5)

    first = cache.refresh()
    assert first["status"] == "ok"
    assert first["count"] == 2
    assert first["added"] == 2
    assert cache.get_market("SERIES-EVENT-001")["yes_bid"] == 40
    assert len(cache.get_event("EVENT")) == 2
    assert len(cache.get_series("SERIES")) == 2
    assert len(cache.get_category("Test")) == 2

    second = cache.refresh()
    assert second["status"] == "ok"
    assert second["count"] == 2
    assert second["added"] == 1
    assert second["changed"] == 1
    assert second["removed"] == 1
    assert cache.get_market("SERIES-EVENT-001")["yes_bid"] == 41
    assert cache.get_market("SERIES-EVENT-002") is None

    stats = cache.statistics()
    assert stats["market_count"] == 2
    assert stats["refresh_count"] == 2
    assert stats["read_only"] is True
    assert len(bus.events) >= 2

    print("[PASS] ADP-013 Live Market Cache & Synchronization Engine")
    print(stats)


if __name__ == "__main__":
    test_adp_013()
'''

init_code = '''try:
    from .live_kalshi_authentication import (
        KalshiAuthConfig,
        KalshiAuthState,
        KalshiAuthError,
        LiveKalshiAuthSession,
        build_live_kalshi_auth_session,
    )
except Exception:
    pass

try:
    from .live_kalshi_market_ingestion import (
        LiveKalshiMarket,
        LiveKalshiMarketIngestion,
        KalshiMarketIngestionError,
        build_live_kalshi_market_ingestion,
    )
except Exception:
    pass

try:
    from .live_market_cache import (
        LiveKalshiMarketCache,
        LiveMarketCacheError,
        build_live_market_cache,
    )
except Exception:
    pass
'''

(ADAPTERS / "live_market_cache.py").write_text(cache_code, encoding="utf-8")
(ADAPTERS / "__init__.py").write_text(init_code, encoding="utf-8")
Path("test_adp_013_live_market_cache.py").write_text(test_code, encoding="utf-8")

print("========================================")
print(" ADP-013 INSTALLER")
print(" Live Market Cache & Synchronization Engine")
print("========================================")
print("[OK] Wrote qseries_v2\\adapters\\live_market_cache.py")
print("[OK] Wrote qseries_v2\\adapters\\__init__.py")
print("[OK] Wrote test_adp_013_live_market_cache.py")
print()
print("[DONE] ADP-013 installed")
print()
print("Run:")
print("python test_adp_013_live_market_cache.py")
print()
print("Optional live cache check:")
print("python -m qseries_v2.adapters.live_market_cache")