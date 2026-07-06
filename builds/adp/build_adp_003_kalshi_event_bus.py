"""
build_adp_003_kalshi_event_bus.py
ADP-003 Kalshi Event Bus Integration Installer
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


integration_code = '''"""
ADP-003 Kalshi Event Bus Integration

Publishes normalized Kalshi markets to the CORE Event Bus.
"""

from qseries_v2.core.event_bus import event_bus
from .kalshi_adapter import kalshi_adapter


class KalshiEventBus:

    def publish_market(self, raw_market):
        market = kalshi_adapter.normalize_market(raw_market)

        payload = {
            "source": market.source,
            "ticker": market.ticker,
            "market": market,
            "evidence": market.as_evidence(),
        }

        event_bus.publish(
            "adapter.kalshi.market",
            payload,
        )

        return payload

    def publish_markets(self, raw_markets):
        return [self.publish_market(item) for item in raw_markets]


kalshi_event_bus = KalshiEventBus()
'''

test_code = '''from qseries_v2.adapters.kalshi_event_bus import kalshi_event_bus
from qseries_v2.core.event_bus import event_bus

events = []

def listener(payload):
    events.append(payload)

event_bus.subscribe("adapter.kalshi.market", listener)

raw = {
    "id": "123",
    "ticker": "TEST-KALSHI",
    "title": "Kalshi Event Bus Test",
    "yes_price": 68,
    "volume": 1000,
}

payload = kalshi_event_bus.publish_market(raw)

assert len(events) == 1
assert payload["ticker"] == "TEST-KALSHI"
assert payload["market"].source == "kalshi"
assert payload["evidence"]["category"] == "market"

print("[PASS] ADP-003 Kalshi Event Bus")
print(payload["evidence"])
'''

init_code = '''from .universal_market_schema import *
from .kalshi_adapter import *
from .kalshi_registry_integration import *
from .kalshi_event_bus import *
'''

print("=" * 40)
print(" ADP-003 INSTALLER")
print(" Kalshi Event Bus")
print("=" * 40)

write(ADP / "kalshi_event_bus.py", integration_code)
write(ADP / "__init__.py", init_code)
write(ROOT / "test_adp_003_kalshi_event_bus.py", test_code)

print("\n[DONE] ADP-003 installed")
print("\nRun:")
print("python test_adp_003_kalshi_event_bus.py")