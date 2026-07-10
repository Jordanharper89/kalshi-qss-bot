
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OracleIntelligenceEngineContract,
    OraclePredictionRequest,
)
from qseries_v2.integration.oracle_engine_registry import OracleEngineRegistry
from qseries_v2.integration.oracle_signal_bus import OracleSignalBus
from qseries_v2.integration.multi_engine_oracle_aggregator import MultiEngineOracleAggregator
from qseries_v2.integration.qseries_execution_gateway import QSeriesExecutionGateway
from qseries_v2.integration.oracle_orchestrator import OracleOrchestrator
from qseries_v2.integration.oracle_terminal_api_layer import OracleTerminalApiLayer


@dataclass(frozen=True)
class OracleRuntimeResult:
    status: str
    endpoint: str
    payload: Dict[str, Any]
    errors: List[str]
    generated_at: str

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OracleIntelligenceRuntime:
    """
    INT-010 Oracle Intelligence Runtime.

    Single canonical runtime entry point for Oracle Intelligence.

    Owns:
    - engine registry
    - signal bus
    - multi-engine aggregator
    - execution gateway
    - orchestrator
    - terminal API

    Oracle remains read-only intelligence.
    Q Series remains the execution layer.
    """

    def __init__(self) -> None:
        self.registry = OracleEngineRegistry()
        self.signal_bus = OracleSignalBus()
        self.aggregator = MultiEngineOracleAggregator()
        self.execution_gateway = QSeriesExecutionGateway()
        self.orchestrator = OracleOrchestrator(
            signal_bus=self.signal_bus,
            aggregator=self.aggregator,
            execution_gateway=self.execution_gateway,
        )
        self.terminal_api = OracleTerminalApiLayer(
            aggregator=self.aggregator,
            execution_gateway=self.execution_gateway,
        )
        self._started = False
        self._started_at: Optional[str] = None

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _result(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        errors: Optional[List[str]] = None,
    ) -> OracleRuntimeResult:
        errors = errors or []
        return OracleRuntimeResult(
            status="ok" if not errors else "error",
            endpoint=endpoint,
            payload=payload,
            errors=errors,
            generated_at=self.now_iso(),
        )

    def start(self) -> OracleRuntimeResult:
        self._started = True
        self._started_at = self.now_iso()
        return self._result(
            "start",
            {
                "started": True,
                "started_at": self._started_at,
                "engine_count": self.registry.count(),
            },
        )

    def stop(self) -> OracleRuntimeResult:
        self._started = False
        return self._result(
            "stop",
            {
                "started": False,
                "stopped_at": self.now_iso(),
            },
        )

    def register_engine(self, engine: OracleIntelligenceEngineContract) -> OracleRuntimeResult:
        try:
            entry = self.registry.register(engine)
            orchestrator_result = self.orchestrator.register_engine(engine)

            if orchestrator_result["status"] != "ok":
                return self._result(
                    "register_engine",
                    {"registry_entry": entry.to_dict(), "orchestrator": orchestrator_result},
                    [orchestrator_result.get("reason", "orchestrator_register_failed")],
                )

            return self._result(
                "register_engine",
                {
                    "registered": True,
                    "engine": entry.to_dict(),
                    "engine_count": self.registry.count(),
                },
            )

        except Exception as exc:
            return self._result(
                "register_engine",
                {"registered": False},
                [str(exc)],
            )

    def run_market(
        self,
        market_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> OracleRuntimeResult:
        if not self._started:
            return self._result(
                "run_market",
                {},
                ["runtime_not_started"],
            )

        result = self.orchestrator.run_market(market_id, payload or {})

        return self._result(
            "run_market",
            result.to_dict(),
            result.errors,
        )

    def predict(
        self,
        market_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> OracleRuntimeResult:
        response = self.terminal_api.predict(market_id, payload or {})
        return self._result(
            "predict",
            response.payload,
            response.errors,
        )

    def decision(
        self,
        market_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> OracleRuntimeResult:
        response = self.terminal_api.decision(market_id, payload or {})
        return self._result(
            "decision",
            response.payload,
            response.errors,
        )

    def explain(
        self,
        market_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> OracleRuntimeResult:
        response = self.terminal_api.explain(market_id, payload or {})
        return self._result(
            "explain",
            response.payload,
            response.errors,
        )

    def engines(self) -> OracleRuntimeResult:
        return self._result(
            "engines",
            {
                "engine_count": self.registry.count(),
                "engines": [entry.to_dict() for entry in self.registry.list_entries()],
            },
        )

    def pipeline_status(self) -> OracleRuntimeResult:
        return self._result(
            "pipeline_status",
            {
                "started": self._started,
                "started_at": self._started_at,
                "registry": self.registry.health(),
                "orchestrator": self.orchestrator.pipeline_status(),
                "terminal_api": self.terminal_api.pipeline_status().to_dict(),
                "signal_bus": self.signal_bus.health(),
                "execution_gateway": self.execution_gateway.health(),
            },
        )

    def health(self) -> OracleRuntimeResult:
        status = "ok" if self._started else "stopped"
        return OracleRuntimeResult(
            status=status,
            endpoint="health",
            payload={
                "runtime": "oracle_intelligence_runtime",
                "started": self._started,
                "started_at": self._started_at,
                "engine_count": self.registry.count(),
                "signal_count": len(self.signal_bus.list_signals()),
                "decision_count": len(self.execution_gateway.list_decisions()),
            },
            errors=[],
            generated_at=self.now_iso(),
        )


def create_oracle_intelligence_runtime() -> OracleIntelligenceRuntime:
    return OracleIntelligenceRuntime()


oracle_intelligence_runtime = create_oracle_intelligence_runtime


__all__ = [
    "OracleRuntimeResult",
    "OracleIntelligenceRuntime",
    "create_oracle_intelligence_runtime",
    "oracle_intelligence_runtime",
]
