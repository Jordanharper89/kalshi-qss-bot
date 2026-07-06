"""
build_adp_004_kalshi_oracle_bridge.py
ADP-004 Kalshi to Oracle Evidence Bridge Installer
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


bridge_code = '''"""
ADP-004 Kalshi to Oracle Evidence Bridge

Converts normalized Kalshi market payloads into Oracle Evidence objects.
"""

from qseries_v2.oi.evidence_engine import Evidence, evidence_engine
from .kalshi_adapter import kalshi_adapter


class KalshiOracleBridge:

    def market_to_evidence(self, raw_market):
        market = kalshi_adapter.normalize_market(raw_market)
        evidence_data = market.as_evidence()

        return Evidence(
            source=evidence_data["source"],
            category=evidence_data["category"],
            value=evidence_data["value"],
        )

    def ingest_market(self, raw_market):
        evidence = self.market_to_evidence(raw_market)
        evidence_engine.add(evidence)
        return evidence

    def ingest_markets(self, raw_markets):
        return [self.ingest_market(item) for item in raw_markets]


kalshi_oracle_bridge = KalshiOracleBridge()
'''

test_code = '''from qseries_v2.adapters.kalshi_oracle_bridge import kalshi_oracle_bridge
from qseries_v2.oi.evidence_engine import evidence_engine, Evidence

raw = {
    "id": "123",
    "ticker": "TEST-KALSHI",
    "title": "Kalshi Oracle Bridge Test",
    "yes_price": 71,
    "volume": 1500,
}

evidence = kalshi_oracle_bridge.ingest_market(raw)

assert isinstance(evidence, Evidence)
assert evidence.source == "kalshi"
assert evidence.category == "market"
assert evidence.value["ticker"] == "TEST-KALSHI"
assert evidence.value["yes_price"] == 71.0
assert len(evidence_engine.all()) >= 1

print("[PASS] ADP-004 Kalshi Oracle Evidence Bridge")
print(evidence)
'''

init_code = '''from .universal_market_schema import *
from .kalshi_adapter import *
from .kalshi_registry_integration import *
from .kalshi_event_bus import *
from .kalshi_oracle_bridge import *
'''

print("=" * 40)
print(" ADP-004 INSTALLER")
print(" Kalshi Oracle Evidence Bridge")
print("=" * 40)

write(ADP / "kalshi_oracle_bridge.py", bridge_code)
write(ADP / "__init__.py", init_code)
write(ROOT / "test_adp_004_kalshi_oracle_bridge.py", test_code)

print("\n[DONE] ADP-004 installed")
print("\nRun:")
print("python test_adp_004_kalshi_oracle_bridge.py")