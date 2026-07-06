"""
build_oi_020_intelligence_bootstrap.py
OI-020 Oracle Intelligence Bootstrap Installer
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


bootstrap_code = '''"""
OI-020 Oracle Intelligence Bootstrap

Single startup entry point for Oracle Intelligence.

Responsibilities:
- Register Oracle Intelligence with Service Registry
- Confirm Oracle API integration
- Confirm diagnostics are healthy
- Return clean boot status for Terminal, Telegram, desktop, mobile, and API users
"""

from .oracle_api_integration import oracle_api_integration
from .intelligence_diagnostics import intelligence_diagnostics_engine


class OracleIntelligenceBootstrap:

    def boot(self):
        api_status = oracle_api_integration.bootstrap()
        diagnostics = intelligence_diagnostics_engine.diagnostics()

        ready = (
            api_status.get("status") == "ready"
            and diagnostics.get("status") == "ok"
            and diagnostics.get("service_registered") is True
        )

        return {
            "module": "OI-020 Oracle Intelligence Bootstrap",
            "status": "ready" if ready else "error",
            "api": api_status,
            "diagnostics": diagnostics,
            "oracle_executes": False,
        }


oracle_intelligence_bootstrap = OracleIntelligenceBootstrap()
'''

test_code = '''from qseries_v2.oi.intelligence_bootstrap import oracle_intelligence_bootstrap

result = oracle_intelligence_bootstrap.boot()

assert result["status"] == "ready"
assert result["api"]["service_id"] == "oracle.intelligence"
assert result["diagnostics"]["service_registered"] is True
assert result["oracle_executes"] is False

print("[PASS] OI-020 Oracle Intelligence Bootstrap")
print({
    "status": result["status"],
    "service_id": result["api"]["service_id"],
    "oracle_executes": result["oracle_executes"],
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
from .intelligence_diagnostics import *
from .intelligence_bootstrap import *
'''

print("=" * 40)
print(" OI-020 INSTALLER")
print(" Oracle Intelligence Bootstrap")
print("=" * 40)

write(OI / "intelligence_bootstrap.py", bootstrap_code)
write(OI / "__init__.py", init_code)
write(ROOT / "test_oi_020_intelligence_bootstrap.py", test_code)

print("\n[DONE] OI-020 installed")
print("\nRun:")
print("python test_oi_020_intelligence_bootstrap.py")