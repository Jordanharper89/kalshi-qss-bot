from qseries_v2.adapters.kalshi_registry_integration import (
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
