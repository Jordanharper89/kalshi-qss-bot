import threading
import time
from datetime import datetime

import requests

from services.base_service import BaseService
from services.market_cache import MarketCache
from services.rate_limiter import RateLimiter


KALSHI_BASE_URL = "https://external-api.kalshi.com/trade-api/v2"


class MarketDataService(BaseService):
    def __init__(self, refresh_interval=5, cache_ttl=15, requests_per_second=5):
        super().__init__("market_data")

        self.refresh_interval = refresh_interval
        self.cache = MarketCache(ttl_seconds=cache_ttl)
        self.rate_limiter = RateLimiter(requests_per_second=requests_per_second)

        self._tickers = set()
        self._tickers_lock = threading.RLock()

        self._subscribers = []
        self._subscribers_lock = threading.RLock()

        self._stop_event = threading.Event()
        self._thread = None

        self.api_calls = 0
        self.refresh_count = 0
        self.errors = 0
        self.last_refresh_at = None
        self.last_error = None

    def start(self):
        if self.running:
            return

        self._stop_event.clear()
        self.mark_started()

        self._thread = threading.Thread(
            target=self._refresh_loop,
            name="MarketDataService",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        if not self.running:
            return

        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        self.mark_stopped()

    def register_ticker(self, ticker):
        if not ticker:
            return

        ticker = str(ticker).upper().strip()

        with self._tickers_lock:
            self._tickers.add(ticker)

    def unregister_ticker(self, ticker):
        if not ticker:
            return

        ticker = str(ticker).upper().strip()

        with self._tickers_lock:
            self._tickers.discard(ticker)

    def registered_tickers(self):
        with self._tickers_lock:
            return sorted(self._tickers)

    def subscribe(self, callback):
        with self._subscribers_lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)

    def unsubscribe(self, callback):
        with self._subscribers_lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

    def get_market(self, ticker, allow_stale=True, refresh_if_missing=True):
        ticker = str(ticker).upper().strip()

        cached = self.cache.get(ticker)
        if cached:
            return cached

        if allow_stale:
            stale = self.cache.get_stale(ticker)
            if stale:
                return stale

        if refresh_if_missing:
            return self.refresh_market(ticker)

        return None

    def get_price(self, ticker):
        market = self.get_market(ticker)
        if not market:
            return None

        return {
            "ticker": ticker.upper(),
            "yes_bid": market.get("yes_bid_dollars"),
            "yes_ask": market.get("yes_ask_dollars"),
            "no_bid": market.get("no_bid_dollars"),
            "no_ask": market.get("no_ask_dollars"),
            "last_price": market.get("last_price_dollars"),
        }

    def refresh_market(self, ticker):
        ticker = str(ticker).upper().strip()

        try:
            market = self._fetch_market(ticker)

            if market:
                self.cache.set(ticker, market)
                self.register_ticker(ticker)
                self._notify_subscribers(ticker, market)

            return market

        except Exception as e:
            self.errors += 1
            self.last_error = str(e)
            return None

    def _fetch_market(self, ticker):
        self.rate_limiter.acquire()

        url = f"{KALSHI_BASE_URL}/markets/{ticker}"
        response = requests.get(url, timeout=20)

        self.api_calls += 1

        if response.status_code == 404:
            return None

        response.raise_for_status()

        data = response.json()
        return data.get("market") or data

    def _refresh_loop(self):
        while not self._stop_event.is_set():
            tickers = self.registered_tickers()

            for ticker in tickers:
                if self._stop_event.is_set():
                    break

                self.refresh_market(ticker)

            self.refresh_count += 1
            self.last_refresh_at = datetime.utcnow()

            self._stop_event.wait(self.refresh_interval)

    def _notify_subscribers(self, ticker, market):
        with self._subscribers_lock:
            subscribers = list(self._subscribers)

        for callback in subscribers:
            try:
                callback(ticker, market)
            except Exception as e:
                self.errors += 1
                self.last_error = f"subscriber error: {e}"

    def diagnostics(self):
        base = super().diagnostics()

        base.update(
            {
                "refresh_interval": self.refresh_interval,
                "registered_tickers": len(self.registered_tickers()),
                "api_calls": self.api_calls,
                "refresh_count": self.refresh_count,
                "errors": self.errors,
                "last_error": self.last_error,
                "last_refresh_at": self.last_refresh_at,
                "cache": self.cache.diagnostics(),
                "rate_limiter": self.rate_limiter.diagnostics(),
                "thread_alive": self._thread.is_alive() if self._thread else False,
            }
        )

        return base


market_data_service = MarketDataService()