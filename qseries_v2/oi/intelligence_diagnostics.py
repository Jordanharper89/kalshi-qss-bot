"""
OI-019 Intelligence Diagnostics Engine

Reports Oracle Intelligence status across pipeline, service registry,
event bus integration, API integration, and learning state.
"""

from .oracle_intelligence_service import oracle_intelligence_service
from .learning_ledger import learning_ledger
from .calibration_engine import calibration_engine
from .performance_review import performance_review_engine
from .service_registry_integration import get_oracle_intelligence
from qseries_v2.core.service_registry import service_registry


class IntelligenceDiagnosticsEngine:

    def diagnostics(self):
        service = get_oracle_intelligence()
        health = oracle_intelligence_service.health()
        review = performance_review_engine.review(learning_ledger.records)
        calibration = calibration_engine.settings()

        return {
            "module": "OI-019 Intelligence Diagnostics Engine",
            "status": "ok",
            "service_registered": service is not None,
            "service_health": health,
            "learning_records": len(learning_ledger.records),
            "performance": review,
            "calibration": calibration,
            "registry": service_registry.diagnostics(),
            "oracle_executes": False,
        }


intelligence_diagnostics_engine = IntelligenceDiagnosticsEngine()
