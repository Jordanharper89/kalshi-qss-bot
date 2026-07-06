"""
ADP-007 Kalshi Adapter Bootstrap

Single startup entry point for Kalshi adapter stack.
"""

from .kalshi_registry_integration import register_kalshi_adapter
from .kalshi_diagnostics import kalshi_diagnostics


class KalshiBootstrap:

    def boot(self):
        record = register_kalshi_adapter(replace=True)
        diagnostics = kalshi_diagnostics.diagnostics()

        ready = (
            record.meta.service_id == "adp.kalshi"
            and diagnostics.get("status") == "ok"
            and diagnostics.get("registered") is True
            and diagnostics.get("market_normalized") is True
            and diagnostics.get("evidence_ready") is True
            and diagnostics.get("analysis_ready") is True
        )

        return {
            "module": "ADP-007 Kalshi Adapter Bootstrap",
            "status": "ready" if ready else "error",
            "service_id": record.meta.service_id,
            "diagnostics": diagnostics,
            "executes_trades": False,
        }


kalshi_bootstrap = KalshiBootstrap()
