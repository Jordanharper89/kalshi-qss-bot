"""
OI-020 Oracle Intelligence Bootstrap

Single startup entry point for Oracle Intelligence.

Responsibilities:
- Register Oracle Intelligence with Service Registry
- Confirm Oracle API integration
- Confirm diagnostics are healthy
- Return clean boot status for Terminal, Telegram, desktop, mobile, and API users
"""

from .oracle_api_integration import oracle_api_integration
from .intelligence_diagnostics import intelligence_diagnostics_engine


class OracleIntelligenceBootstrap:

    def boot(self):
        api_status = oracle_api_integration.bootstrap()
        diagnostics = intelligence_diagnostics_engine.diagnostics()

        ready = (
            api_status.get("status") == "ready"
            and diagnostics.get("status") == "ok"
            and diagnostics.get("service_registered") is True
        )

        return {
            "module": "OI-020 Oracle Intelligence Bootstrap",
            "status": "ready" if ready else "error",
            "api": api_status,
            "diagnostics": diagnostics,
            "oracle_executes": False,
        }


oracle_intelligence_bootstrap = OracleIntelligenceBootstrap()
