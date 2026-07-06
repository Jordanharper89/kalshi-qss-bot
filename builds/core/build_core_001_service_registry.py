# build_core_001_service_registry.py
from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2"
CORE = PKG / "core"

FILES = {
    PKG / "__init__.py": '''"""Q Series V2 package."""\n''',

    CORE / "__init__.py": '''"""
Q Series V2 Core Architecture

CORE modules:
- Service Registry
- Plugin Architecture
- Event Bus
- Shared Models
- Oracle API Layer
"""
from .service_registry import service_registry, ServiceRegistry
''',

    CORE / "service_contracts.py": '''"""
CORE-001 — Service Contracts

Defines the standard contract every internal service must follow.
Oracle, Q Series, adapters, UI layers, and research engines should register
through the Service Registry instead of directly depending on each other.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional


@dataclass
class ServiceMeta:
    service_id: str
    name: str
    category: str
    version: str = "1.0.0"
    description: str = ""
    status: str = "registered"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: list[str] = field(default_factory=list)


@dataclass
class ServiceRecord:
    meta: ServiceMeta
    instance: Any = None
    healthcheck: Optional[Callable[[], Dict[str, Any]]] = None

    def health(self) -> Dict[str, Any]:
        if self.healthcheck:
            try:
                result = self.healthcheck()
                if not isinstance(result, dict):
                    return {"ok": False, "error": "healthcheck did not return dict"}
                return {"ok": True, **result}
            except Exception as exc:
                return {"ok": False, "error": str(exc)}

        return {"ok": True, "status": self.meta.status}
''',

    CORE / "service_registry.py": '''"""
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
''',

    ROOT / "test_core_001_service_registry.py": '''"""
Smoke test for CORE-001 Service Registry.
Run:
    python test_core_001_service_registry.py
"""

from qseries_v2.core.service_registry import service_registry


class DemoOracleService:
    def status(self):
        return "ready"


def demo_healthcheck():
    return {
        "status": "ready",
        "message": "Demo service healthcheck passed",
    }


service_registry.register(
    service_id="oracle.demo",
    name="Demo Oracle Intelligence Service",
    category="OI",
    instance=DemoOracleService(),
    version="0.1.0",
    description="Demo service proving CORE-001 registry works.",
    healthcheck=demo_healthcheck,
    tags=["demo", "oracle", "core-001"],
    replace=True,
)

print("SERVICE LIST:")
for service in service_registry.list_services():
    print(service)

print("\\nHEALTH:")
print(service_registry.health())

print("\\nDIAGNOSTICS:")
print(service_registry.diagnostics())

svc = service_registry.get("oracle.demo")
print("\\nDIRECT SERVICE LOOKUP:")
print(svc.status())
''',
}


def backup(path: Path):
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.with_suffix(path.suffix + f".bak_{stamp}")
        backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        return backup_path
    return None


def main():
    print("===================================")
    print(" CORE-001 INSTALLER")
    print(" Core Service Registry")
    print("===================================")

    if not PKG.exists():
        PKG.mkdir(parents=True, exist_ok=True)

    CORE.mkdir(parents=True, exist_ok=True)

    for path, content in FILES.items():
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            backup_path = backup(path)
            print(f"Backup created: {backup_path}")

        path.write_text(content, encoding="utf-8")
        print(f"[OK] Wrote {path.relative_to(ROOT)}")

    print("")
    print("[DONE] CORE-001 Service Registry installed")
    print("")
    print("Test:")
    print(" python test_core_001_service_registry.py")


if __name__ == "__main__":
    main()