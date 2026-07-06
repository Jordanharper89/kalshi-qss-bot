"""
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
