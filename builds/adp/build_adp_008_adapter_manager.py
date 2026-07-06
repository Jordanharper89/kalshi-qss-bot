"""
build_adp_008_adapter_manager.py
ADP-008 Adapter Manager Installer
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


manager_code = '''"""
ADP-008 Adapter Manager

Central manager for market adapters.
Adapters normalize markets and feed Oracle.
Adapters do not execute trades.
"""

class AdapterManager:

    def __init__(self):
        self.adapters = {}

    def register(self, adapter_id, adapter, replace=False):
        if adapter_id in self.adapters and not replace:
            raise ValueError(f"Adapter already registered: {adapter_id}")

        self.adapters[adapter_id] = adapter
        return adapter

    def get(self, adapter_id):
        return self.adapters.get(adapter_id)

    def list_adapters(self):
        return sorted(self.adapters.keys())

    def health(self):
        rows = {}

        for adapter_id, adapter in self.adapters.items():
            if hasattr(adapter, "health"):
                rows[adapter_id] = adapter.health()
            else:
                rows[adapter_id] = {"status": "unknown"}

        return {
            "status": "ok",
            "adapter_count": len(self.adapters),
            "adapters": rows,
            "executes_trades": False,
        }


adapter_manager = AdapterManager()
'''

test_code = '''from qseries_v2.adapters.adapter_manager import adapter_manager
from qseries_v2.adapters.kalshi_adapter import kalshi_adapter

adapter_manager.register("adp.kalshi", kalshi_adapter, replace=True)

assert adapter_manager.get("adp.kalshi") is not None
assert "adp.kalshi" in adapter_manager.list_adapters()

health = adapter_manager.health()

assert health["status"] == "ok"
assert health["adapter_count"] == 1
assert health["executes_trades"] is False

print("[PASS] ADP-008 Adapter Manager")
print(health)
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
'''

print("=" * 40)
print(" ADP-008 INSTALLER")
print(" Adapter Manager")
print("=" * 40)

write(ADP / "adapter_manager.py", manager_code)
write(ADP / "__init__.py", init_code)
write(ROOT / "test_adp_008_adapter_manager.py", test_code)

print("\n[DONE] ADP-008 installed")
print("\nRun:")
print("python test_adp_008_adapter_manager.py")