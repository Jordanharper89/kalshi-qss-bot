"""
Oracle Service Registry

ORACLE-022.2

Purpose:
- Central dependency container.
- Registers and retrieves Oracle services.
- Eliminates circular imports.
"""

from typing import Any, Dict


class OracleServiceRegistry:
    def __init__(self):
        self._services: Dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        if not name:
            raise ValueError("Service name cannot be empty.")

        self._services[name] = service

    def get(self, name: str) -> Any:
        if name not in self._services:
            raise KeyError(f"Oracle service '{name}' is not registered.")

        return self._services[name]

    def exists(self, name: str) -> bool:
        return name in self._services

    def unregister(self, name: str) -> None:
        self._services.pop(name, None)

    def clear(self) -> None:
        self._services.clear()

    def list_services(self):
        return sorted(self._services.keys())

    def snapshot(self):
        return {
            "registered_services": self.list_services(),
            "count": len(self._services),
        }


oracle_services = OracleServiceRegistry()