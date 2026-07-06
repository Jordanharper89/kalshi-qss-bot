"""
build_oi_018_oracle_api_integration.py
OI-018 Oracle API Integration Installer
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
OI-018 Oracle API Integration

Exposes Oracle Intelligence through the CORE Oracle API Layer.
Oracle researches, scores, explains, and learns.
Oracle never executes trades.
"""

from qseries_v2.core.oracle_api import oracle_api
from .service_registry_integration import register_oracle_intelligence
from .event_bus_integration import oracle_event_bus


class OracleAPIIntegration:

    def __init__(self):
        self.service_id = "oracle.intelligence"

    def bootstrap(self):
        record = register_oracle_intelligence(replace=True)
        return {
            "status": "ready",
            "service_id": record.meta.service_id,
            "name": record.meta.name,
            "category": record.meta.category,
            "version": record.meta.version,
            "oracle_executes": False,
        }

    def analyze(self, ticker, market_yes_price, evidence):
        return oracle_event_bus.analyze(
            ticker=ticker,
            market_yes_price=market_yes_price,
            evidence=evidence,
        )

    def get_service(self):
        return oracle_api.get_service(self.service_id)

    def publish(self, event_name, payload=None):
        return oracle_api.publish(event_name, payload)

    def subscribe(self, event_name, callback):
        return oracle_api.subscribe(event_name, callback)


oracle_api_integration = OracleAPIIntegration()
'''

test_code = '''from qseries_v2.oi.evidence_engine import Evidence
from qseries_v2.oi.oracle_api_integration import oracle_api_integration

boot = oracle_api_integration.bootstrap()

evidence = [
    Evidence(source="Market", category="market", value={"move": "up"}),
    Evidence(source="News", category="news", value={"tone": "positive"}),
    Evidence(source="History", category="historical", value={"pattern": "matched"}),
]

packet = oracle_api_integration.analyze(
    ticker="TEST-MARKET",
    market_yes_price=80,
    evidence=evidence,
)

service = oracle_api_integration.get_service()

assert boot["status"] == "ready"
assert boot["service_id"] == "oracle.intelligence"
assert packet["packet_type"] == "oracle_research_packet"
assert packet["oracle_executes"] is False
assert service is not None

print("[PASS] OI-018 Oracle API Integration")
print({
    "boot": boot,
    "ticker": packet["ticker"],
    "action": packet["action"],
    "confidence": packet["confidence"],
})
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
from .oracle_api_integration import *
'''

print("=" * 40)
print(" OI-018 INSTALLER")
print(" Oracle API Integration")
print("=" * 40)

write(OI / "oracle_api_integration.py", integration_code)
write(OI / "__init__.py", init_code)
write(ROOT / "test_oi_018_oracle_api_integration.py", test_code)

print("\n[DONE] OI-018 installed")
print("\nRun:")
print("python test_oi_018_oracle_api_integration.py")