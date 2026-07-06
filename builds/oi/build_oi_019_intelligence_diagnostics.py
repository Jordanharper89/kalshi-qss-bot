"""
build_oi_019_intelligence_diagnostics.py
OI-019 Intelligence Diagnostics Engine Installer
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


diagnostics_code = '''"""
OI-019 Intelligence Diagnostics Engine

Reports Oracle Intelligence status across pipeline, service registry,
event bus integration, API integration, and learning state.
"""

from .oracle_intelligence_service import oracle_intelligence_service
from .learning_ledger import learning_ledger
from .calibration_engine import calibration_engine
from .performance_review import performance_review_engine
from .service_registry_integration import get_oracle_intelligence
from qseries_v2.core.service_registry import service_registry


class IntelligenceDiagnosticsEngine:

    def diagnostics(self):
        service = get_oracle_intelligence()
        health = oracle_intelligence_service.health()
        review = performance_review_engine.review(learning_ledger.records)
        calibration = calibration_engine.settings()

        return {
            "module": "OI-019 Intelligence Diagnostics Engine",
            "status": "ok",
            "service_registered": service is not None,
            "service_health": health,
            "learning_records": len(learning_ledger.records),
            "performance": review,
            "calibration": calibration,
            "registry": service_registry.diagnostics(),
            "oracle_executes": False,
        }


intelligence_diagnostics_engine = IntelligenceDiagnosticsEngine()
'''

test_code = '''from qseries_v2.oi.service_registry_integration import register_oracle_intelligence
from qseries_v2.oi.intelligence_diagnostics import intelligence_diagnostics_engine

register_oracle_intelligence(replace=True)

diag = intelligence_diagnostics_engine.diagnostics()

assert diag["status"] == "ok"
assert diag["service_registered"] is True
assert diag["oracle_executes"] is False
assert "performance" in diag
assert "calibration" in diag

print("[PASS] OI-019 Intelligence Diagnostics Engine")
print(diag)
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
from .intelligence_diagnostics import *
'''

print("=" * 40)
print(" OI-019 INSTALLER")
print(" Intelligence Diagnostics Engine")
print("=" * 40)

write(OI / "intelligence_diagnostics.py", diagnostics_code)
write(OI / "__init__.py", init_code)
write(ROOT / "test_oi_019_intelligence_diagnostics.py", test_code)

print("\n[DONE] OI-019 installed")
print("\nRun:")
print("python test_oi_019_intelligence_diagnostics.py")