"""
CORE-005 Oracle API Layer
"""

from .service_registry import service_registry
from .event_bus import event_bus

class OracleAPI:

    def get_service(self, service_id):
        return service_registry.get(service_id)

    def publish(self, event_name, payload=None):
        event_bus.publish(event_name, payload)

    def subscribe(self, event_name, callback):
        event_bus.subscribe(event_name, callback)

oracle_api = OracleAPI()
