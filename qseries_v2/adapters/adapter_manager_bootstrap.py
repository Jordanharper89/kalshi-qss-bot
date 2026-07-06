"""
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
