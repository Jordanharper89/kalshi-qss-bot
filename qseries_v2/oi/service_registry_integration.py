"""
OI-016 Oracle Service Registry Integration

Registers Oracle Intelligence with CORE-001 Service Registry.
"""

from qseries_v2.core.service_registry import service_registry
from .oracle_intelligence_service import oracle_intelligence_service


def register_oracle_intelligence(replace=True):
    return service_registry.register(
        service_id=oracle_intelligence_service.service_id,
        name=oracle_intelligence_service.name,
        category=oracle_intelligence_service.category,
        instance=oracle_intelligence_service,
        version=oracle_intelligence_service.version,
        description="Oracle Intelligence researches, scores, explains, and learns. Oracle never executes trades.",
        healthcheck=oracle_intelligence_service.health,
        tags=["oracle", "intelligence", "research", "learning"],
        replace=replace,
    )


def get_oracle_intelligence():
    return service_registry.get(oracle_intelligence_service.service_id)
