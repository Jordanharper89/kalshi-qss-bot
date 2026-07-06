"""
OI-018 Oracle API Integration

Exposes Oracle Intelligence through the CORE Oracle API Layer.
Oracle researches, scores, explains, and learns.
Oracle never executes trades.
"""

from qseries_v2.core.oracle_api import oracle_api
from .service_registry_integration import register_oracle_intelligence
from .event_bus_integration import oracle_event_bus


class OracleAPIIntegration:

    def __init__(self):
        self.service_id = "oracle.intelligence"

    def bootstrap(self):
        record = register_oracle_intelligence(replace=True)
        return {
            "status": "ready",
            "service_id": record.meta.service_id,
            "name": record.meta.name,
            "category": record.meta.category,
            "version": record.meta.version,
            "oracle_executes": False,
        }

    def analyze(self, ticker, market_yes_price, evidence):
        return oracle_event_bus.analyze(
            ticker=ticker,
            market_yes_price=market_yes_price,
            evidence=evidence,
        )

    def get_service(self):
        return oracle_api.get_service(self.service_id)

    def publish(self, event_name, payload=None):
        return oracle_api.publish(event_name, payload)

    def subscribe(self, event_name, callback):
        return oracle_api.subscribe(event_name, callback)


oracle_api_integration = OracleAPIIntegration()
