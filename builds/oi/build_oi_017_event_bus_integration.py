"""
build_oi_017_event_bus_integration.py
OI-017 Event Bus Integration Installer
"""

from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
OI = ROOT / "qseries_v2" / "oi"


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
OI-017 Event Bus Integration

Publishes Oracle Intelligence events onto the CORE Event Bus.
"""

from qseries_v2.core.event_bus import event_bus
from .oracle_intelligence_service import oracle_intelligence_service


class OracleEventBusIntegration:

    def analyze(self, ticker, market_yes_price, evidence):
        packet = oracle_intelligence_service.analyze(
            ticker=ticker,
            market_yes_price=market_yes_price,
            evidence=evidence,
        )

        event_bus.publish(
            "oracle.analysis.completed",
            {
                "ticker": packet["ticker"],
                "action": packet["action"],
                "confidence": packet["confidence"],
                "packet": packet,
            },
        )

        return packet

    def resolve(self, ticker, outcome):
        result = oracle_intelligence_service.resolve(ticker, outcome)

        event_bus.publish(
            "oracle.market.resolved",
            {
                "ticker": ticker,
                "outcome": outcome,
            },
        )

        return result


oracle_event_bus = OracleEventBusIntegration()
'''

test_code = '''from qseries_v2.oi.evidence_engine import Evidence
from qseries_v2.oi.event_bus_integration import oracle_event_bus
from qseries_v2.core.event_bus import event_bus

events = []

def handler(payload):
    events.append(payload)

event_bus.subscribe("oracle.analysis.completed", handler)

evidence = [
    Evidence(source="Market", category="market", value={"move":"up"}),
    Evidence(source="News", category="news", value={"tone":"positive"}),
    Evidence(source="History", category="historical", value={"pattern":"matched"}),
]

packet = oracle_event_bus.analyze(
    ticker="TEST-MARKET",
    market_yes_price=80,
    evidence=evidence,
)

assert len(events) == 1
assert events[0]["ticker"] == "TEST-MARKET"
assert packet["action"] == "BUY_YES"

print("[PASS] OI-017 Event Bus Integration")
print(events[0])
'''

init_code = '''from .evidence_engine import *
from .confidence_engine import *
from .probability_engine import *
from .recommendation_engine import *
from .explanation_engine import *
from .decision_pipeline import *
from .learning_ledger import *
from .performance_review import *
from .learning_feedback import *
from .learning_loop import *
from .calibration_engine import *
from .calibrated_pipeline import *
from .research_report import *
from .research_packet import *
from .oracle_intelligence_service import *
from .service_registry_integration import *
from .event_bus_integration import *
'''

print("=" * 40)
print(" OI-017 INSTALLER")
print(" Event Bus Integration")
print("=" * 40)

write(OI / "event_bus_integration.py", integration_code)
write(OI / "__init__.py", init_code)
write(ROOT / "test_oi_017_event_bus_integration.py", test_code)

print("\n[DONE] OI-017 installed")
print("\nRun:")
print("python test_oi_017_event_bus_integration.py")