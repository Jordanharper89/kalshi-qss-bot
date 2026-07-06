"""
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
