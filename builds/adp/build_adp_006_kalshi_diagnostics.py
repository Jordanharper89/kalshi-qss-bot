"""
build_adp_006_kalshi_diagnostics.py
ADP-006 Kalshi Adapter Diagnostics Installer
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


diagnostics_code = '''"""
ADP-006 Kalshi Adapter Diagnostics

Checks Kalshi adapter health, registry state, normalization, evidence bridge,
and analysis bridge readiness.
"""

from qseries_v2.core.service_registry import service_registry
from .kalshi_adapter import kalshi_adapter
from .kalshi_registry_integration import register_kalshi_adapter, get_kalshi_adapter
from .kalshi_oracle_bridge import kalshi_oracle_bridge
from .kalshi_analysis_bridge import kalshi_analysis_bridge


class KalshiDiagnostics:

    def diagnostics(self):
        register_kalshi_adapter(replace=True)
        registered = get_kalshi_adapter() is not None

        raw = {
            "id": "diag_001",
            "ticker": "KALSHI-DIAG",
            "title": "Kalshi Diagnostics Test",
            "yes_price": 62,
            "volume": 100,
            "liquidity": 50,
            "status": "open",
        }

        market = kalshi_adapter.normalize_market(raw)
        evidence = kalshi_oracle_bridge.market_to_evidence(raw)
        analysis = kalshi_analysis_bridge.analyze_market(raw)

        return {
            "module": "ADP-006 Kalshi Adapter Diagnostics",
            "status": "ok",
            "adapter_health": kalshi_adapter.health(),
            "registered": registered,
            "registry_health": service_registry.health("adp.kalshi"),
            "market_normalized": market.ticker == "KALSHI-DIAG",
            "evidence_ready": evidence.category == "market",
            "analysis_ready": analysis["packet"]["ticker"] == "KALSHI-DIAG",
            "oracle_executes": False,
        }


kalshi_diagnostics = KalshiDiagnostics()
'''

test_code = '''from qseries_v2.adapters.kalshi_diagnostics import kalshi_diagnostics

diag = kalshi_diagnostics.diagnostics()

assert diag["status"] == "ok"
assert diag["registered"] is True
assert diag["market_normalized"] is True
assert diag["evidence_ready"] is True
assert diag["analysis_ready"] is True
assert diag["oracle_executes"] is False

print("[PASS] ADP-006 Kalshi Diagnostics")
print(diag)
'''

init_code = '''from .universal_market_schema import *
from .kalshi_adapter import *
from .kalshi_registry_integration import *
from .kalshi_event_bus import *
from .kalshi_oracle_bridge import *
from .kalshi_analysis_bridge import *
from .kalshi_diagnostics import *
'''

print("=" * 40)
print(" ADP-006 INSTALLER")
print(" Kalshi Diagnostics")
print("=" * 40)

write(ADP / "kalshi_diagnostics.py", diagnostics_code)
write(ADP / "__init__.py", init_code)
write(ROOT / "test_adp_006_kalshi_diagnostics.py", test_code)

print("\n[DONE] ADP-006 installed")
print("\nRun:")
print("python test_adp_006_kalshi_diagnostics.py")