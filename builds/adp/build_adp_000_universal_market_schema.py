"""
build_adp_000_universal_market_schema.py
ADP-000 Universal Market Schema Installer
"""

from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
ADP = ROOT / "qseries_v2" / "adapters"


def backup(path):
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = path.with_suffix(path.suffix + f".bak_{stamp}")
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup(path)
    path.write_text(text, encoding="utf-8")
    print(f"[OK] Wrote {path.relative_to(ROOT)}")


schema_code = '''"""
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
'''

test_code = '''from qseries_v2.adapters.universal_market_schema import universal_market_schema, UniversalMarket

market = universal_market_schema.create(
    source="kalshi",
    market_id="123",
    ticker="TEST-MARKET",
    title="Will this test pass?",
    yes_price=0.72,
    volume=1000,
    liquidity=500,
    raw={"demo": True},
)

assert isinstance(market, UniversalMarket)
assert market.yes_price == 72.0
assert market.no_price == 28.0
assert market.implied_probability() == 0.72

evidence = market.as_evidence()

assert evidence["category"] == "market"
assert evidence["value"]["ticker"] == "TEST-MARKET"

print("[PASS] ADP-000 Universal Market Schema")
print(evidence)
'''

init_code = '''from .universal_market_schema import (
    UniversalMarket,
    UniversalMarketSchema,
    universal_market_schema,
)
'''

print("=" * 40)
print(" ADP-000 INSTALLER")
print(" Universal Market Schema")
print("=" * 40)

write(ADP / "__init__.py", init_code)
write(ADP / "universal_market_schema.py", schema_code)
write(ROOT / "test_adp_000_universal_market_schema.py", test_code)

print("\n[DONE] ADP-000 installed")
print("\nRun:")
print("python test_adp_000_universal_market_schema.py")