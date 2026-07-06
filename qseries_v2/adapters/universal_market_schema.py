"""
ADP-000 Universal Market Schema

Every market adapter converts raw platform data into this common Oracle format.
Oracle Intelligence should consume standardized market objects, not raw exchange data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class UniversalMarket:
    source: str
    market_id: str
    ticker: str
    title: str
    category: str = "unknown"
    status: str = "unknown"

    yes_price: Optional[float] = None
    no_price: Optional[float] = None
    last_price: Optional[float] = None
    volume: Optional[float] = None
    liquidity: Optional[float] = None
    open_interest: Optional[float] = None

    close_time: str = ""
    event_ticker: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)
    normalized_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def implied_probability(self):
        if self.yes_price is None:
            return None
        return round(float(self.yes_price) / 100.0, 4)

    def as_evidence(self):
        return {
            "source": self.source,
            "category": "market",
            "value": {
                "market_id": self.market_id,
                "ticker": self.ticker,
                "title": self.title,
                "yes_price": self.yes_price,
                "no_price": self.no_price,
                "last_price": self.last_price,
                "volume": self.volume,
                "liquidity": self.liquidity,
                "open_interest": self.open_interest,
                "implied_probability": self.implied_probability(),
                "status": self.status,
            },
        }


class UniversalMarketSchema:

    def normalize_price(self, value):
        if value is None:
            return None
        try:
            value = float(value)
            if value <= 1:
                value *= 100
            return round(value, 2)
        except Exception:
            return None

    def create(
        self,
        source,
        market_id,
        ticker,
        title,
        category="unknown",
        status="unknown",
        yes_price=None,
        no_price=None,
        last_price=None,
        volume=None,
        liquidity=None,
        open_interest=None,
        close_time="",
        event_ticker="",
        raw=None,
    ):
        yes = self.normalize_price(yes_price)
        no = self.normalize_price(no_price)

        if no is None and yes is not None:
            no = round(100 - yes, 2)

        return UniversalMarket(
            source=source,
            market_id=str(market_id),
            ticker=str(ticker),
            title=str(title),
            category=category,
            status=status,
            yes_price=yes,
            no_price=no,
            last_price=self.normalize_price(last_price),
            volume=volume,
            liquidity=liquidity,
            open_interest=open_interest,
            close_time=close_time,
            event_ticker=event_ticker,
            raw=raw or {},
        )


universal_market_schema = UniversalMarketSchema()
