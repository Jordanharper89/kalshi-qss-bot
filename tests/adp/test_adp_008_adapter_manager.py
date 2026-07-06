from qseries_v2.adapters.adapter_manager import adapter_manager
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
