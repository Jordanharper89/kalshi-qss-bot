"""
build_adp_002_kalshi_registry_integration.py
ADP-002 Kalshi Adapter Service Registry Integration Installer
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


integration_code = '''"""
ADP-002 Kalshi Adapter Service Registry Integration

Registers the Kalshi Adapter with CORE-001 Service Registry.
"""

from qseries_v2.core.service_registry import service_registry
from .kalshi_adapter import kalshi_adapter


def register_kalshi_adapter(replace=True):
    return service_registry.register(
        service_id=kalshi_adapter.adapter_id,
        name="Kalshi Adapter",
        category="ADP",
        instance=kalshi_adapter,
        version=kalshi_adapter.version,
        description="Normalizes Kalshi market data into Oracle UniversalMarket format. Does not execute trades.",
        healthcheck=kalshi_adapter.health,
        tags=["adapter", "kalshi", "market-data"],
        replace=replace,
    )


def get_kalshi_adapter():
    return service_registry.get(kalshi_adapter.adapter_id)
'''

test_code = '''from qseries_v2.adapters.kalshi_registry_integration import (
    register_kalshi_adapter,
    get_kalshi_adapter,
)
from qseries_v2.core.service_registry import service_registry

record = register_kalshi_adapter(replace=True)
adapter = get_kalshi_adapter()
health = service_registry.health("adp.kalshi")

assert record.meta.service_id == "adp.kalshi"
assert adapter is not None
assert health["health"]["ok"] is True
assert health["health"]["executes_trades"] is False

print("[PASS] ADP-002 Kalshi Registry Integration")
print(service_registry.diagnostics())
'''

init_code = '''from .universal_market_schema import (
    UniversalMarket,
    UniversalMarketSchema,
    universal_market_schema,
)
from .kalshi_adapter import kalshi_adapter, KalshiAdapter
from .kalshi_registry_integration import register_kalshi_adapter, get_kalshi_adapter
'''

print("=" * 40)
print(" ADP-002 INSTALLER")
print(" Kalshi Registry Integration")
print("=" * 40)

write(ADP / "kalshi_registry_integration.py", integration_code)
write(ADP / "__init__.py", init_code)
write(ROOT / "test_adp_002_kalshi_registry_integration.py", test_code)

print("\n[DONE] ADP-002 installed")
print("\nRun:")
print("python test_adp_002_kalshi_registry_integration.py")