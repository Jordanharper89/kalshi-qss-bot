"""
ADP-006 Kalshi Adapter Diagnostics

Checks Kalshi adapter health, registry state, normalization, evidence bridge,
and analysis bridge readiness.
"""

from qseries_v2.core.service_registry import service_registry
from .kalshi_adapter import kalshi_adapter
from .kalshi_registry_integration import register_kalshi_adapter, get_kalshi_adapter
from .kalshi_oracle_bridge import kalshi_oracle_bridge
from .kalshi_analysis_bridge import kalshi_analysis_bridge


class KalshiDiagnostics:

    def diagnostics(self):
        register_kalshi_adapter(replace=True)
        registered = get_kalshi_adapter() is not None

        raw = {
            "id": "diag_001",
            "ticker": "KALSHI-DIAG",
            "title": "Kalshi Diagnostics Test",
            "yes_price": 62,
            "volume": 100,
            "liquidity": 50,
            "status": "open",
        }

        market = kalshi_adapter.normalize_market(raw)
        evidence = kalshi_oracle_bridge.market_to_evidence(raw)
        analysis = kalshi_analysis_bridge.analyze_market(raw)

        return {
            "module": "ADP-006 Kalshi Adapter Diagnostics",
            "status": "ok",
            "adapter_health": kalshi_adapter.health(),
            "registered": registered,
            "registry_health": service_registry.health("adp.kalshi"),
            "market_normalized": market.ticker == "KALSHI-DIAG",
            "evidence_ready": evidence.category == "market",
            "analysis_ready": analysis["packet"]["ticker"] == "KALSHI-DIAG",
            "oracle_executes": False,
        }


kalshi_diagnostics = KalshiDiagnostics()
