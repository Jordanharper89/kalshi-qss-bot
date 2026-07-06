"""
CORE-001 — Core Service Registry

Purpose:
- Central registry for all Oracle/Q Series services.
- Prevent direct engine-to-engine coupling.
- Allow every engine, adapter, API, and UI module to be replaceable.
- Provide discovery, diagnostics, and health reporting.

Rule:
No engine should directly import another engine for business communication.
Engines should register here and communicate through approved architecture:
Service Registry, Event Bus, or Oracle API.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .service_contracts import ServiceMeta, ServiceRecord


class ServiceRegistry:
    def __init__(self):
        self._services: Dict[str, ServiceRecord] = {}

    def register(
        self,
        service_id: str,
        name: str,
        category: str,
        instance: Any = None,
        version: str = "1.0.0",
        description: str = "",
        healthcheck: Optional[Callable[[], Dict[str, Any]]] = None,
        tags: Optional[List[str]] = None,
        replace: bool = False,
    ) -> ServiceRecord:
        if not service_id:
            raise ValueError("service_id is required")

        if service_id in self._services and not replace:
            raise ValueError(f"Service already registered: {service_id}")

        meta = ServiceMeta(
            service_id=service_id,
            name=name,
            category=category,
            version=version,
            description=description,
            tags=tags or [],
        )

        record = ServiceRecord(
            meta=meta,
            instance=instance,
            healthcheck=healthcheck,
        )

        self._services[service_id] = record
        return record

    def unregister(self, service_id: str) -> bool:
        return self._services.pop(service_id, None) is not None

    def get(self, service_id: str) -> Any:
        record = self._services.get(service_id)
        return record.instance if record else None

    def get_record(self, service_id: str) -> Optional[ServiceRecord]:
        return self._services.get(service_id)

    def exists(self, service_id: str) -> bool:
        return service_id in self._services

    def list_services(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        rows = []

        for record in self._services.values():
            if category and record.meta.category != category:
                continue

            rows.append(
                {
                    "service_id": record.meta.service_id,
                    "name": record.meta.name,
                    "category": record.meta.category,
                    "version": record.meta.version,
                    "status": record.meta.status,
                    "description": record.meta.description,
                    "tags": record.meta.tags,
                    "created_at": record.meta.created_at,
                }
            )

        return sorted(rows, key=lambda x: (x["category"], x["service_id"]))

    def categories(self) -> List[str]:
        return sorted({record.meta.category for record in self._services.values()})

    def health(self, service_id: Optional[str] = None) -> Dict[str, Any]:
        if service_id:
            record = self._services.get(service_id)
            if not record:
                return {"ok": False, "error": f"Service not found: {service_id}"}

            return {
                "service_id": service_id,
                "name": record.meta.name,
                "category": record.meta.category,
                "health": record.health(),
            }

        results = {}
        ok = True

        for sid, record in self._services.items():
            health = record.health()
            results[sid] = {
                "name": record.meta.name,
                "category": record.meta.category,
                "health": health,
            }
            if not health.get("ok", False):
                ok = False

        return {
            "ok": ok,
            "service_count": len(self._services),
            "categories": self.categories(),
            "services": results,
        }

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": "CORE-001 Service Registry",
            "status": "ok",
            "service_count": len(self._services),
            "categories": self.categories(),
            "services": self.list_services(),
        }


service_registry = ServiceRegistry()
