"""
build_adp_007_kalshi_bootstrap.py
ADP-007 Kalshi Adapter Bootstrap Installer
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


bootstrap_code = '''"""
ADP-007 Kalshi Adapter Bootstrap

Single startup entry point for Kalshi adapter stack.
"""

from .kalshi_registry_integration import register_kalshi_adapter
from .kalshi_diagnostics import kalshi_diagnostics


class KalshiBootstrap:

    def boot(self):
        record = register_kalshi_adapter(replace=True)
        diagnostics = kalshi_diagnostics.diagnostics()

        ready = (
            record.meta.service_id == "adp.kalshi"
            and diagnostics.get("status") == "ok"
            and diagnostics.get("registered") is True
            and diagnostics.get("market_normalized") is True
            and diagnostics.get("evidence_ready") is True
            and diagnostics.get("analysis_ready") is True
        )

        return {
            "module": "ADP-007 Kalshi Adapter Bootstrap",
            "status": "ready" if ready else "error",
            "service_id": record.meta.service_id,
            "diagnostics": diagnostics,
            "executes_trades": False,
        }


kalshi_bootstrap = KalshiBootstrap()
'''

test_code = '''from qseries_v2.adapters.kalshi_bootstrap import kalshi_bootstrap

result = kalshi_bootstrap.boot()

assert result["status"] == "ready"
assert result["service_id"] == "adp.kalshi"
assert result["executes_trades"] is False
assert result["diagnostics"]["status"] == "ok"

print("[PASS] ADP-007 Kalshi Bootstrap")
print({
    "status": result["status"],
    "service_id": result["service_id"],
    "executes_trades": result["executes_trades"],
})
'''

init_code = '''from .universal_market_schema import *
from .kalshi_adapter import *
from .kalshi_registry_integration import *
from .kalshi_event_bus import *
from .kalshi_oracle_bridge import *
from .kalshi_analysis_bridge import *
from .kalshi_diagnostics import *
from .kalshi_bootstrap import *
'''

print("=" * 40)
print(" ADP-007 INSTALLER")
print(" Kalshi Bootstrap")
print("=" * 40)

write(ADP / "kalshi_bootstrap.py", bootstrap_code)
write(ADP / "__init__.py", init_code)
write(ROOT / "test_adp_007_kalshi_bootstrap.py", test_code)

print("\n[DONE] ADP-007 installed")
print("\nRun:")
print("python test_adp_007_kalshi_bootstrap.py")