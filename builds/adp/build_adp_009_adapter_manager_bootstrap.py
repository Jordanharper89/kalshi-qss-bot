"""
build_adp_009_adapter_manager_bootstrap.py
ADP-009 Adapter Manager Bootstrap Installer
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
ADP-009 Adapter Manager Bootstrap

Boots all available adapters into the Adapter Manager.
"""

from .adapter_manager import adapter_manager
from .kalshi_adapter import kalshi_adapter
from .kalshi_bootstrap import kalshi_bootstrap


class AdapterManagerBootstrap:

    def boot(self):
        kalshi_status = kalshi_bootstrap.boot()
        adapter_manager.register("adp.kalshi", kalshi_adapter, replace=True)

        health = adapter_manager.health()

        ready = (
            kalshi_status.get("status") == "ready"
            and health.get("status") == "ok"
            and "adp.kalshi" in adapter_manager.list_adapters()
        )

        return {
            "module": "ADP-009 Adapter Manager Bootstrap",
            "status": "ready" if ready else "error",
            "kalshi": kalshi_status,
            "adapter_manager": health,
            "executes_trades": False,
        }


adapter_manager_bootstrap = AdapterManagerBootstrap()
'''

test_code = '''from qseries_v2.adapters.adapter_manager_bootstrap import adapter_manager_bootstrap

result = adapter_manager_bootstrap.boot()

assert result["status"] == "ready"
assert result["adapter_manager"]["adapter_count"] >= 1
assert "adp.kalshi" in result["adapter_manager"]["adapters"]
assert result["executes_trades"] is False

print("[PASS] ADP-009 Adapter Manager Bootstrap")
print({
    "status": result["status"],
    "adapter_count": result["adapter_manager"]["adapter_count"],
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
from .adapter_manager import *
from .adapter_manager_bootstrap import *
'''

print("=" * 40)
print(" ADP-009 INSTALLER")
print(" Adapter Manager Bootstrap")
print("=" * 40)

write(ADP / "adapter_manager_bootstrap.py", bootstrap_code)
write(ADP / "__init__.py", init_code)
write(ROOT / "test_adp_009_adapter_manager_bootstrap.py", test_code)

print("\n[DONE] ADP-009 installed")
print("\nRun:")
print("python test_adp_009_adapter_manager_bootstrap.py")