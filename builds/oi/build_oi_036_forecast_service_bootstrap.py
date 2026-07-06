from pathlib import Path
import textwrap

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
TEST_FILE = ROOT / "test_oi_036_forecast_service_bootstrap.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

BOOTSTRAP = OI_DIR / "forecast_service_bootstrap.py"

BOOTSTRAP.write_text(textwrap.dedent(r'''
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
''').strip() + "\n", encoding="utf-8")

TEST_FILE.write_text(textwrap.dedent(r'''
from qseries_v2.oracle_intelligence.forecast_service_bootstrap import (
    ForecastServiceBootstrap,
    bootstrap_forecast_service,
)


class FakeService:
    def diagnostics(self):
        return {
            "module": "fake_forecast_service",
            "status": "ok",
            "read_only": True,
            "execution_allowed": False,
        }


def test_oi_036_forecast_service_bootstrap():
    bootstrap = ForecastServiceBootstrap(service=FakeService())

    before = bootstrap.diagnostics()
    assert before["status"] == "not_booted"
    assert before["booted"] is False
    assert before["service_ready"] is True
    assert before["read_only"] is True
    assert before["execution_allowed"] is False

    status = bootstrap.bootstrap()
    assert status["status"] == "ok"
    assert status["booted"] is True
    assert status["service_ready"] is True
    assert status["service_diagnostics"]["status"] == "ok"
    assert status["read_only"] is True
    assert status["execution_allowed"] is False

    payload = bootstrap.api_payload()
    assert payload["status"] == "ok"
    assert payload["booted"] is True
    assert payload["service_ready"] is True

    global_status = bootstrap_forecast_service()
    assert global_status["read_only"] is True
    assert global_status["execution_allowed"] is False

    print("[PASS] OI-036 Forecast Service Bootstrap")
    print({
        "status": status["status"],
        "booted": status["booted"],
        "service_ready": status["service_ready"],
    })


if __name__ == "__main__":
    test_oi_036_forecast_service_bootstrap()
''').strip() + "\n", encoding="utf-8")

INIT = OI_DIR / "__init__.py"
content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""

line = "from .forecast_service_bootstrap import ForecastServiceBootstrap, oracle_forecast_service_bootstrap, bootstrap_forecast_service\n"
if line not in content:
    content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")

print("========================================")
print(" OI-036 INSTALLER")
print(" Forecast Service Bootstrap")
print("========================================")
print(f"[OK] Wrote {BOOTSTRAP}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT}")
print("")
print("[DONE] OI-036 installed")
print("")
print("Run:")
print("python test_oi_036_forecast_service_bootstrap.py")