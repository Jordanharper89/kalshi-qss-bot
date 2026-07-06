"""
Oracle Discovery Worker

KQ-018.3B

Purpose:
- Fetch active markets from Market Data Service.
- Run Oracle Market Discovery.
- Skip already watched tickers.
- Add discovered candidates to Oracle Watchlist.
- Return a structured summary.

Oracle does NOT execute trades.
Oracle does NOT send Telegram alerts directly.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from oracle_market_discovery import discover_oracle_markets


class OracleDiscoveryWorker:
    def __init__(
        self,
        market_data_service: Any,
        watchlist_service: Any,
        preferred_categories: Optional[List[str]] = None,
        min_volume: float = 100.0,
        min_liquidity: float = 100.0,
        max_candidates: int = 25,
        auto_add_limit: int = 10,
    ):
        self.market_data_service = market_data_service
        self.watchlist_service = watchlist_service
        self.preferred_categories = preferred_categories or []
        self.min_volume = min_volume
        self.min_liquidity = min_liquidity
        self.max_candidates = max_candidates
        self.auto_add_limit = auto_add_limit

    def run_once(self) -> Dict[str, Any]:
        raw_markets = self._fetch_markets()
        watched_tickers = self._get_watched_tickers()

        discovered = discover_oracle_markets(
            raw_markets=raw_markets,
            already_watched_tickers=watched_tickers,
            min_volume=self.min_volume,
            min_liquidity=self.min_liquidity,
            max_candidates=self.max_candidates,
            preferred_categories=self.preferred_categories,
        )

        added = []
        skipped = []

        for candidate in discovered[: self.auto_add_limit]:
            ticker = candidate.get("ticker")

            if not ticker:
                skipped.append(
                    {
                        "ticker": None,
                        "status": "SKIPPED",
                        "reason": "Missing ticker",
                    }
                )
                continue

            if ticker in watched_tickers:
                skipped.append(
                    {
                        "ticker": ticker,
                        "status": "SKIPPED",
                        "reason": "Already watched",
                    }
                )
                continue

            success = self._add_to_watchlist(candidate)

            if success:
                watched_tickers.add(ticker)
                added.append(
                    {
                        "ticker": ticker,
                        "title": candidate.get("title"),
                        "category": candidate.get("category"),
                        "discovery_score": candidate.get("discovery_score"),
                        "discovery_reasons": candidate.get("discovery_reasons", []),
                    }
                )
            else:
                skipped.append(
                    {
                        "ticker": ticker,
                        "status": "SKIPPED",
                        "reason": "Watchlist add failed",
                    }
                )

        return {
            "status": "OK",
            "raw_markets": len(raw_markets),
            "already_watched": len(watched_tickers),
            "discovered": len(discovered),
            "added": len(added),
            "skipped": len(skipped),
            "added_markets": added,
            "skipped_markets": skipped,
            "ran_at": self._utc_now(),
        }

    def _fetch_markets(self) -> List[Dict[str, Any]]:
        if hasattr(self.market_data_service, "get_markets"):
            markets = self.market_data_service.get_markets()
            return markets or []

        if hasattr(self.market_data_service, "list_markets"):
            markets = self.market_data_service.list_markets()
            return markets or []

        if hasattr(self.market_data_service, "fetch_markets"):
            markets = self.market_data_service.fetch_markets()
            return markets or []

        raise AttributeError(
            "Market Data Service must provide get_markets(), list_markets(), or fetch_markets()."
        )

    def _get_watched_tickers(self) -> Set[str]:
        watched = []

        if hasattr(self.watchlist_service, "list_watched_markets"):
            watched = self.watchlist_service.list_watched_markets() or []

        elif hasattr(self.watchlist_service, "get_all"):
            watched = self.watchlist_service.get_all() or []

        elif hasattr(self.watchlist_service, "list_all"):
            watched = self.watchlist_service.list_all() or []

        tickers: Set[str] = set()

        for item in watched:
            if isinstance(item, str):
                tickers.add(item.strip())
            elif isinstance(item, dict):
                ticker = (
                    item.get("ticker")
                    or item.get("market_ticker")
                    or item.get("symbol")
                )
                if ticker:
                    tickers.add(str(ticker).strip())

        return tickers

    def _add_to_watchlist(self, candidate: Dict[str, Any]) -> bool:
        ticker = candidate.get("ticker")

        payload = {
            "ticker": ticker,
            "title": candidate.get("title"),
            "category": candidate.get("category"),
            "status": "WATCHING",
            "source": "ORACLE_DISCOVERY",
            "discovery_score": candidate.get("discovery_score"),
            "discovery_reasons": candidate.get("discovery_reasons", []),
            "discovered_at": candidate.get("discovered_at"),
            "added_to_watchlist_at": self._utc_now(),
            "raw_market": candidate.get("raw_market", {}),
        }

        if hasattr(self.watchlist_service, "add_market"):
            self.watchlist_service.add_market(payload)
            return True

        if hasattr(self.watchlist_service, "watch"):
            self.watchlist_service.watch(ticker, payload)
            return True

        if hasattr(self.watchlist_service, "add"):
            self.watchlist_service.add(payload)
            return True

        raise AttributeError(
            "Watchlist Service must provide add_market(), watch(), or add()."
        )

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


def run_oracle_discovery_cycle(
    market_data_service: Any,
    watchlist_service: Any,
    preferred_categories: Optional[List[str]] = None,
    min_volume: float = 100.0,
    min_liquidity: float = 100.0,
    max_candidates: int = 25,
    auto_add_limit: int = 10,
) -> Dict[str, Any]:
    worker = OracleDiscoveryWorker(
        market_data_service=market_data_service,
        watchlist_service=watchlist_service,
        preferred_categories=preferred_categories,
        min_volume=min_volume,
        min_liquidity=min_liquidity,
        max_candidates=max_candidates,
        auto_add_limit=auto_add_limit,
    )

    return worker.run_once()