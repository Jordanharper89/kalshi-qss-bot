from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


class ForecastServiceBootstrap:
    def __init__(self, service=None):
        self.service = service
        self.booted = False
        self.booted_at: Optional[str] = None
        self.last_status: Dict[str, Any] = {}

        if self.service is None:
            try:
                from .forecast_intelligence_service import oracle_forecast_intelligence_service
                self.service = oracle_forecast_intelligence_service
            except Exception:
                pass

    def bootstrap(self) -> Dict[str, Any]:
        diagnostics = {}

        if self.service is not None and hasattr(self.service, "diagnostics"):
            diagnostics = self.service.diagnostics()

        self.booted = self.service is not None
        self.booted_at = self._now() if self.booted else None

        self.last_status = {
            "module": "OI-036 Forecast Service Bootstrap",
            "status": "ok" if self.booted else "missing_forecast_service",
            "booted": self.booted,
            "booted_at": self.booted_at,
            "service_ready": self.service is not None,
            "service_diagnostics": diagnostics,
            "read_only": True,
            "execution_allowed": False,
        }

        return self.last_status

    def diagnostics(self) -> Dict[str, Any]:
        if not self.last_status:
            return {
                "module": "OI-036 Forecast Service Bootstrap",
                "status": "not_booted",
                "booted": False,
                "service_ready": self.service is not None,
                "read_only": True,
                "execution_allowed": False,
            }

        return self.last_status

    def get_service(self):
        return self.service

    def api_payload(self) -> Dict[str, Any]:
        status = self.diagnostics()
        return {
            "module": "oracle_forecast_service_bootstrap_payload",
            "status": status.get("status"),
            "booted": status.get("booted"),
            "service_ready": status.get("service_ready"),
            "read_only": True,
            "execution_allowed": False,
        }

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_forecast_service_bootstrap = ForecastServiceBootstrap()


def bootstrap_forecast_service() -> Dict[str, Any]:
    return oracle_forecast_service_bootstrap.bootstrap()
