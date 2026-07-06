"""
build_adp_005_kalshi_analysis_bridge.py
ADP-005 Kalshi Oracle Analysis Bridge Installer
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
ADP-005 Kalshi Oracle Analysis Bridge

Takes raw Kalshi market data, converts it into Oracle Evidence,
then runs Oracle Intelligence analysis and returns a research packet.
"""

from .kalshi_adapter import kalshi_adapter
from .kalshi_oracle_bridge import kalshi_oracle_bridge
from qseries_v2.oi.oracle_api_integration import oracle_api_integration


class KalshiAnalysisBridge:

    def analyze_market(self, raw_market):
        market = kalshi_adapter.normalize_market(raw_market)
        evidence = kalshi_oracle_bridge.market_to_evidence(raw_market)

        packet = oracle_api_integration.analyze(
            ticker=market.ticker,
            market_yes_price=market.yes_price or 0,
            evidence=[evidence],
        )

        return {
            "source": "kalshi",
            "market": market,
            "evidence": evidence,
            "packet": packet,
            "oracle_executes": False,
        }

    def analyze_markets(self, raw_markets):
        return [self.analyze_market(item) for item in raw_markets]


kalshi_analysis_bridge = KalshiAnalysisBridge()
'''

test_code = '''from qseries_v2.adapters.kalshi_analysis_bridge import kalshi_analysis_bridge

raw = {
    "id": "123",
    "ticker": "TEST-KALSHI",
    "title": "Kalshi Analysis Bridge Test",
    "yes_price": 71,
    "volume": 1500,
}

result = kalshi_analysis_bridge.analyze_market(raw)

assert result["source"] == "kalshi"
assert result["market"].ticker == "TEST-KALSHI"
assert result["evidence"].category == "market"
assert result["packet"]["ticker"] == "TEST-KALSHI"
assert result["oracle_executes"] is False
assert result["packet"]["oracle_executes"] is False

print("[PASS] ADP-005 Kalshi Oracle Analysis Bridge")
print({
    "ticker": result["packet"]["ticker"],
    "action": result["packet"]["action"],
    "confidence": result["packet"]["confidence"],
    "oracle_executes": result["oracle_executes"],
})
'''

init_code = '''from .universal_market_schema import *
from .kalshi_adapter import *
from .kalshi_registry_integration import *
from .kalshi_event_bus import *
from .kalshi_oracle_bridge import *
from .kalshi_analysis_bridge import *
'''

print("=" * 40)
print(" ADP-005 INSTALLER")
print(" Kalshi Oracle Analysis Bridge")
print("=" * 40)

write(ADP / "kalshi_analysis_bridge.py", bridge_code)
write(ADP / "__init__.py", init_code)
write(ROOT / "test_adp_005_kalshi_analysis_bridge.py", test_code)

print("\n[DONE] ADP-005 installed")
print("\nRun:")
print("python test_adp_005_kalshi_analysis_bridge.py")