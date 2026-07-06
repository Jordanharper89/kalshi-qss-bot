"""
Oracle Market Discovery Engine

KQ-018.3

Purpose:
- Scan raw Kalshi market data.
- Find promising markets automatically.
- Score discovery candidates.
- Return structured candidate markets.
- Does NOT execute trades.
- Does NOT send Telegram alerts.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set


@dataclass
class OracleDiscoveredMarket:
    ticker: str
    title: str
    category: str
    status: str
    yes_price: float
    no_price: float
    volume: float
    liquidity: float
    open_interest: float
    expiration_time: str
    discovery_score: float
    discovery_reasons: List[str]
    discovered_at: str
    raw_market: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OracleMarketDiscovery:
    """
    Finds promising markets from a list of raw market dictionaries.

    Expected input:
        List[Dict] from Kalshi Market Data Service / GET markets.

    Output:
        List[Dict] candidate markets sorted by discovery_score.
    """

    def __init__(
        self,
        min_volume: float = 100.0,
        min_liquidity: float = 100.0,
        max_candidates: int = 25,
        preferred_categories: Optional[List[str]] = None,
    ):
        self.min_volume = min_volume
        self.min_liquidity = min_liquidity
        self.max_candidates = max_candidates
        self.preferred_categories = [
            item.lower().strip()
            for item in (preferred_categories or [])
            if str(item).strip()
        ]

    def discover(
        self,
        raw_markets: List[Dict[str, Any]],
        already_watched_tickers: Optional[Set[str]] = None,
    ) -> List[Dict[str, Any]]:
        already_watched_tickers = already_watched_tickers or set()

        candidates: List[OracleDiscoveredMarket] = []

        for market in raw_markets:
            ticker = self._get_ticker(market)

            if not ticker:
                continue

            if ticker in already_watched_tickers:
                continue

            if not self._is_market_active(market):
                continue

            volume = self._get_volume(market)
            liquidity = self._get_liquidity(market)

            if volume < self.min_volume and liquidity < self.min_liquidity:
                continue

            candidate = self._build_candidate(market)

            if not candidate:
                continue

            if candidate.discovery_score <= 0:
                continue

            candidates.append(candidate)

        candidates.sort(key=lambda item: item.discovery_score, reverse=True)

        return [
            candidate.to_dict()
            for candidate in candidates[: self.max_candidates]
        ]

    def _build_candidate(
        self,
        market: Dict[str, Any],
    ) -> Optional[OracleDiscoveredMarket]:
        ticker = self._get_ticker(market)
        title = self._get_title(market)
        category = self._get_category(market)
        status = self._get_status(market)
        yes_price = self._get_yes_price(market)
        no_price = self._get_no_price(market)
        volume = self._get_volume(market)
        liquidity = self._get_liquidity(market)
        open_interest = self._get_open_interest(market)
        expiration_time = self._get_expiration_time(market)

        discovery_score, discovery_reasons = self._score_market(
            market=market,
            category=category,
            yes_price=yes_price,
            no_price=no_price,
            volume=volume,
            liquidity=liquidity,
            open_interest=open_interest,
            expiration_time=expiration_time,
        )

        return OracleDiscoveredMarket(
            ticker=ticker,
            title=title,
            category=category,
            status=status,
            yes_price=yes_price,
            no_price=no_price,
            volume=volume,
            liquidity=liquidity,
            open_interest=open_interest,
            expiration_time=expiration_time,
            discovery_score=round(discovery_score, 2),
            discovery_reasons=discovery_reasons,
            discovered_at=self._utc_now(),
            raw_market=market,
        )

    def _score_market(
        self,
        market: Dict[str, Any],
        category: str,
        yes_price: float,
        no_price: float,
        volume: float,
        liquidity: float,
        open_interest: float,
        expiration_time: str,
    ) -> tuple[float, List[str]]:
        score = 0.0
        reasons: List[str] = []

        volume_score = self._score_volume(volume)
        if volume_score:
            score += volume_score
            reasons.append(f"Volume activity detected: {volume:.0f}")

        liquidity_score = self._score_liquidity(liquidity)
        if liquidity_score:
            score += liquidity_score
            reasons.append(f"Liquidity available: {liquidity:.0f}")

        open_interest_score = self._score_open_interest(open_interest)
        if open_interest_score:
            score += open_interest_score
            reasons.append(f"Open interest present: {open_interest:.0f}")

        price_score, price_reason = self._score_price_structure(yes_price, no_price)
        if price_score:
            score += price_score
            reasons.append(price_reason)

        expiration_score, expiration_reason = self._score_expiration(expiration_time)
        if expiration_score:
            score += expiration_score
            reasons.append(expiration_reason)

        category_score = self._score_category(category)
        if category_score:
            score += category_score
            reasons.append(f"Preferred category match: {category}")

        movement_score, movement_reason = self._score_market_movement(market)
        if movement_score:
            score += movement_score
            reasons.append(movement_reason)

        spread_score, spread_reason = self._score_spread(market)
        if spread_score:
            score += spread_score
            reasons.append(spread_reason)

        score = max(0.0, min(100.0, score))

        if not reasons:
            reasons.append("Passed basic discovery filters")

        return score, reasons

    def _score_volume(self, volume: float) -> float:
        if volume >= 100000:
            return 20.0
        if volume >= 50000:
            return 16.0
        if volume >= 10000:
            return 12.0
        if volume >= 1000:
            return 8.0
        if volume >= self.min_volume:
            return 4.0
        return 0.0

    def _score_liquidity(self, liquidity: float) -> float:
        if liquidity >= 100000:
            return 18.0
        if liquidity >= 50000:
            return 14.0
        if liquidity >= 10000:
            return 10.0
        if liquidity >= 1000:
            return 6.0
        if liquidity >= self.min_liquidity:
            return 3.0
        return 0.0

    def _score_open_interest(self, open_interest: float) -> float:
        if open_interest >= 100000:
            return 12.0
        if open_interest >= 50000:
            return 9.0
        if open_interest >= 10000:
            return 6.0
        if open_interest >= 1000:
            return 3.0
        return 0.0

    def _score_price_structure(
        self,
        yes_price: float,
        no_price: float,
    ) -> tuple[float, str]:
        if yes_price <= 0 and no_price <= 0:
            return 0.0, ""

        score = 0.0
        reasons = []

        if 20 <= yes_price <= 80:
            score += 6.0
            reasons.append("YES price in tradable range")

        if 20 <= no_price <= 80:
            score += 6.0
            reasons.append("NO price in tradable range")

        if yes_price <= 15 or yes_price >= 85:
            score += 3.0
            reasons.append("Extreme YES probability")

        if no_price <= 15 or no_price >= 85:
            score += 3.0
            reasons.append("Extreme NO probability")

        return score, ", ".join(reasons)

    def _score_expiration(
        self,
        expiration_time: str,
    ) -> tuple[float, str]:
        expiration_dt = self._parse_datetime(expiration_time)

        if not expiration_dt:
            return 0.0, ""

        now = datetime.now(timezone.utc)
        minutes_left = (expiration_dt - now).total_seconds() / 60

        if minutes_left <= 0:
            return 0.0, ""

        if minutes_left <= 30:
            return 12.0, "Near expiration: under 30 minutes"
        if minutes_left <= 120:
            return 10.0, "Near expiration: under 2 hours"
        if minutes_left <= 360:
            return 7.0, "Same-session expiration window"
        if minutes_left <= 1440:
            return 4.0, "Expires within 24 hours"

        return 1.0, "Longer-dated active market"

    def _score_category(self, category: str) -> float:
        if not self.preferred_categories:
            return 0.0

        category_lower = category.lower().strip()

        for preferred in self.preferred_categories:
            if preferred and preferred in category_lower:
                return 10.0

        return 0.0

    def _score_market_movement(
        self,
        market: Dict[str, Any],
    ) -> tuple[float, str]:
        movement = self._safe_float(
            market.get("price_change")
            or market.get("yes_price_change")
            or market.get("change_24h")
            or market.get("probability_change"),
            default=0.0,
        )

        abs_movement = abs(movement)

        if abs_movement >= 20:
            return 12.0, f"Large market movement: {movement:.2f}"
        if abs_movement >= 10:
            return 8.0, f"Meaningful market movement: {movement:.2f}"
        if abs_movement >= 5:
            return 4.0, f"Moderate market movement: {movement:.2f}"

        return 0.0, ""

    def _score_spread(
        self,
        market: Dict[str, Any],
    ) -> tuple[float, str]:
        bid = self._safe_float(
            market.get("yes_bid")
            or market.get("best_yes_bid")
            or market.get("bid"),
            default=None,
        )

        ask = self._safe_float(
            market.get("yes_ask")
            or market.get("best_yes_ask")
            or market.get("ask"),
            default=None,
        )

        if bid is None or ask is None:
            return 0.0, ""

        spread = abs(ask - bid)

        if spread <= 1:
            return 8.0, f"Tight spread: {spread:.2f}c"
        if spread <= 3:
            return 5.0, f"Tradable spread: {spread:.2f}c"
        if spread <= 5:
            return 2.0, f"Acceptable spread: {spread:.2f}c"

        return 0.0, ""

    def _is_market_active(self, market: Dict[str, Any]) -> bool:
        status = self._get_status(market).lower()

        if status in ("closed", "settled", "expired", "finalized"):
            return False

        if market.get("is_closed") is True:
            return False

        if market.get("settled") is True:
            return False

        expiration = self._get_expiration_time(market)
        expiration_dt = self._parse_datetime(expiration)

        if expiration_dt and expiration_dt <= datetime.now(timezone.utc):
            return False

        return True

    def _get_ticker(self, market: Dict[str, Any]) -> str:
        return str(
            market.get("ticker")
            or market.get("market_ticker")
            or market.get("symbol")
            or ""
        ).strip()

    def _get_title(self, market: Dict[str, Any]) -> str:
        return str(
            market.get("title")
            or market.get("name")
            or market.get("subtitle")
            or market.get("event_title")
            or ""
        ).strip()

    def _get_category(self, market: Dict[str, Any]) -> str:
        return str(
            market.get("category")
            or market.get("category_name")
            or market.get("event_category")
            or market.get("series_ticker")
            or "UNKNOWN"
        ).strip()

    def _get_status(self, market: Dict[str, Any]) -> str:
        return str(
            market.get("status")
            or market.get("market_status")
            or "active"
        ).strip()

    def _get_yes_price(self, market: Dict[str, Any]) -> float:
        return self._safe_float(
            market.get("yes_price")
            or market.get("last_price")
            or market.get("last_yes_price")
            or market.get("yes_ask")
            or market.get("best_yes_ask"),
            default=0.0,
        )

    def _get_no_price(self, market: Dict[str, Any]) -> float:
        return self._safe_float(
            market.get("no_price")
            or market.get("last_no_price")
            or market.get("no_ask")
            or market.get("best_no_ask"),
            default=0.0,
        )

    def _get_volume(self, market: Dict[str, Any]) -> float:
        return self._safe_float(
            market.get("volume")
            or market.get("volume_24h")
            or market.get("daily_volume")
            or market.get("total_volume"),
            default=0.0,
        )

    def _get_liquidity(self, market: Dict[str, Any]) -> float:
        return self._safe_float(
            market.get("liquidity")
            or market.get("dollar_liquidity")
            or market.get("notional_value")
            or market.get("open_interest"),
            default=0.0,
        )

    def _get_open_interest(self, market: Dict[str, Any]) -> float:
        return self._safe_float(
            market.get("open_interest")
            or market.get("oi"),
            default=0.0,
        )

    def _get_expiration_time(self, market: Dict[str, Any]) -> str:
        return str(
            market.get("expiration_time")
            or market.get("close_time")
            or market.get("end_time")
            or market.get("expected_expiration_time")
            or ""
        ).strip()

    def _safe_float(self, value: Any, default: Optional[float] = 0.0) -> Optional[float]:
        try:
            if value is None:
                return default

            if isinstance(value, str):
                value = (
                    value.replace("%", "")
                    .replace("c", "")
                    .replace("¢", "")
                    .replace(",", "")
                    .strip()
                )

            return float(value)

        except (TypeError, ValueError):
            return default

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        if not value:
            return None

        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value

        if not isinstance(value, str):
            return None

        cleaned = value.strip()

        try:
            if cleaned.endswith("Z"):
                cleaned = cleaned.replace("Z", "+00:00")

            parsed = datetime.fromisoformat(cleaned)

            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)

            return parsed

        except ValueError:
            return None

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


def discover_oracle_markets(
    raw_markets: List[Dict[str, Any]],
    already_watched_tickers: Optional[Set[str]] = None,
    min_volume: float = 100.0,
    min_liquidity: float = 100.0,
    max_candidates: int = 25,
    preferred_categories: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    discovery = OracleMarketDiscovery(
        min_volume=min_volume,
        min_liquidity=min_liquidity,
        max_candidates=max_candidates,
        preferred_categories=preferred_categories,
    )

    return discovery.discover(
        raw_markets=raw_markets,
        already_watched_tickers=already_watched_tickers,
    )


if __name__ == "__main__":
    sample_markets = [
        {
            "ticker": "KXBTC-TEST",
            "title": "Will Bitcoin be above $100,000 today?",
            "category": "Crypto",
            "status": "active",
            "yes_price": 55,
            "no_price": 45,
            "volume": 125000,
            "liquidity": 70000,
            "open_interest": 50000,
            "expiration_time": "2026-06-28T00:00:00+00:00",
            "price_change": 12,
            "yes_bid": 54,
            "yes_ask": 55,
        },
        {
            "ticker": "KXLOW-TEST",
            "title": "Low activity market",
            "category": "Misc",
            "status": "active",
            "yes_price": 51,
            "no_price": 49,
            "volume": 5,
            "liquidity": 12,
            "expiration_time": "2026-06-30T00:00:00+00:00",
        },
        {
            "ticker": "KXFED-TEST",
            "title": "Will the Fed cut rates?",
            "category": "Economy",
            "status": "active",
            "yes_price": 22,
            "no_price": 78,
            "volume": 45000,
            "liquidity": 38000,
            "open_interest": 12000,
            "expiration_time": "2026-06-27T23:00:00+00:00",
            "price_change": -7,
            "yes_bid": 21,
            "yes_ask": 23,
        },
    ]

    discovered = discover_oracle_markets(
        raw_markets=sample_markets,
        already_watched_tickers=set(),
        preferred_categories=["crypto", "economy", "sports"],
    )

    for market in discovered:
        print(
            market["ticker"],
            market["discovery_score"],
            market["discovery_reasons"],
        )