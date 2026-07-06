"""
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
