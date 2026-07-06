"""
build_adp_001_kalshi_adapter.py
ADP-001 Kalshi Adapter Installer
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


adapter_code = '''"""
ADP-001 Kalshi Adapter

Converts Kalshi-style market data into Oracle's UniversalMarket format.
This adapter does NOT execute trades.
"""

from .universal_market_schema import universal_market_schema


class KalshiAdapter:

    source = "kalshi"
    adapter_id = "adp.kalshi"
    version = "0.1.0"

    def normalize_market(self, raw):
        market_id = raw.get("id") or raw.get("market_id") or raw.get("ticker")
        ticker = raw.get("ticker") or raw.get("market_ticker") or market_id
        title = raw.get("title") or raw.get("subtitle") or raw.get("name") or ticker

        yes_price = (
            raw.get("yes_price")
            or raw.get("yes_bid")
            or raw.get("last_price")
            or raw.get("yes_ask")
        )

        no_price = (
            raw.get("no_price")
            or raw.get("no_bid")
            or raw.get("no_ask")
        )

        return universal_market_schema.create(
            source=self.source,
            market_id=market_id,
            ticker=ticker,
            title=title,
            category=raw.get("category", "unknown"),
            status=raw.get("status", "unknown"),
            yes_price=yes_price,
            no_price=no_price,
            last_price=raw.get("last_price"),
            volume=raw.get("volume"),
            liquidity=raw.get("liquidity"),
            open_interest=raw.get("open_interest"),
            close_time=raw.get("close_time", ""),
            event_ticker=raw.get("event_ticker", ""),
            raw=raw,
        )

    def normalize_markets(self, raw_markets):
        return [self.normalize_market(item) for item in raw_markets]

    def health(self):
        return {
            "status": "ready",
            "adapter_id": self.adapter_id,
            "source": self.source,
            "version": self.version,
            "executes_trades": False,
        }


kalshi_adapter = KalshiAdapter()
'''

test_code = '''from qseries_v2.adapters.kalshi_adapter import kalshi_adapter

raw = {
    "id": "mkt_123",
    "ticker": "KXTEST-YES",
    "title": "Will this Kalshi adapter test pass?",
    "yes_price": 64,
    "volume": 2500,
    "liquidity": 1200,
    "status": "open",
}

market = kalshi_adapter.normalize_market(raw)
health = kalshi_adapter.health()

assert market.source == "kalshi"
assert market.ticker == "KXTEST-YES"
assert market.yes_price == 64.0
assert market.no_price == 36.0
assert health["executes_trades"] is False

print("[PASS] ADP-001 Kalshi Adapter")
print(market.as_evidence())
print(health)
'''

init_code = '''from .universal_market_schema import (
    UniversalMarket,
    UniversalMarketSchema,
    universal_market_schema,
)
from .kalshi_adapter import kalshi_adapter, KalshiAdapter
'''

print("=" * 40)
print(" ADP-001 INSTALLER")
print(" Kalshi Adapter")
print("=" * 40)

write(ADP / "kalshi_adapter.py", adapter_code)
write(ADP / "__init__.py", init_code)
write(ROOT / "test_adp_001_kalshi_adapter.py", test_code)

print("\n[DONE] ADP-001 installed")
print("\nRun:")
print("python test_adp_001_kalshi_adapter.py")