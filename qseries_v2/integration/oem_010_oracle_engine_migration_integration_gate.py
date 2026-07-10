"""
OEM-010 Oracle Engine Migration Integration Gate

Validates migrated Oracle Engine Migration adapters against the canonical
Oracle Integration architecture.

Oracle remains read-only.
Q Series remains execution-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib import import_module
from typing import Any, Dict, List, Optional


GATE_ID = "oracle.engine_migration.integration_gate"
GATE_NAME = "Oracle Engine Migration Integration Gate"
GATE_VERSION = "OEM-010"


EXPECTED_ADAPTERS = [
    {
        "module": "qseries_v2.integration.oem_003_market_relationship_engine_adapter",
        "class_name": "MarketRelationshipEngineAdapter",
        "engine_id": "oracle.market_relationship",
    },
    {
        "module": "qseries_v2.integration.oem_004_market_influence_engine_adapter",
        "class_name": "MarketInfluenceEngineAdapter",
        "engine_id": "oracle.market_influence",
    },
    {
        "module": "qseries_v2.integration.oem_005_market_sentiment_engine_adapter",
        "class_name": "MarketSentimentEngineAdapter",
        "engine_id": "oracle.market_sentiment",
    },
    {
        "module": "qseries_v2.integration.oem_006_discovery_engine_adapter",
        "class_name": "DiscoveryEngineAdapter",
        "engine_id": "oracle.discovery",
    },
    {
        "module": "qseries_v2.integration.oem_007_recall_ledger_engine_adapter",
        "class_name": "RecallLedgerEngineAdapter",
        "engine_id": "oracle.recall_ledger",
    },
    {
        "module": "qseries_v2.integration.oem_008_query_audit_engine_adapter",
        "class_name": "QueryAuditEngineAdapter",
        "engine_id": "oracle.query_audit",
    },
    {
        "module": "qseries_v2.integration.oem_009_query_resolver_engine_adapter",
        "class_name": "QueryResolverEngineAdapter",
        "engine_id": "oracle.query_resolver",
    },
]


OPTIONAL_ADAPTERS = [
    {
        "module": "qseries_v2.integration.oem_001_historical_pattern_recognition_engine_adapter",
        "class_name": "HistoricalPatternRecognitionEngineAdapter",
        "engine_id": "oracle.historical_pattern_recognition",
    },
    {
        "module": "qseries_v2.integration.oem_002_historical_outcome_tracking_engine_adapter",
        "class_name": "HistoricalOutcomeTrackingEngineAdapter",
        "engine_id": "oracle.historical_outcome_tracking",
    },
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class GateCheck:
    engine_id: str
    module: str
    class_name: str
    status: str
    read_only: bool = False
    health_status: Optional[str] = None
    signal_count: int = 0
    prediction_count: int = 0
    error: Optional[str] = None
    checked_at: str = field(default_factory=_utc_now)


@dataclass
class GateResult:
    gate_id: str
    status: str
    required_count: int
    passed_count: int
    failed_count: int
    optional_loaded_count: int
    checks: List[Dict[str, Any]]
    telemetry: Dict[str, Any]
    generated_at: str = field(default_factory=_utc_now)


class OracleEngineMigrationIntegrationGate:
    gate_id = GATE_ID
    name = GATE_NAME
    version = GATE_VERSION
    read_only = True

    def __init__(self, runtime_paths: Optional[Any] = None):
        self.runtime_paths = runtime_paths

    def run(self) -> GateResult:
        checks: List[GateCheck] = []

        for spec in EXPECTED_ADAPTERS:
            checks.append(self._check_adapter(spec, required=True))

        optional_loaded_count = 0
        for spec in OPTIONAL_ADAPTERS:
            check = self._check_adapter(spec, required=False)
            if check.status == "pass":
                optional_loaded_count += 1
                checks.append(check)

        passed_count = sum(1 for check in checks if check.status == "pass" and check.engine_id in self._required_engine_ids())
        failed_count = sum(1 for check in checks if check.status == "fail" and check.engine_id in self._required_engine_ids())

        status = "pass" if failed_count == 0 and passed_count == len(EXPECTED_ADAPTERS) else "fail"

        return GateResult(
            gate_id=self.gate_id,
            status=status,
            required_count=len(EXPECTED_ADAPTERS),
            passed_count=passed_count,
            failed_count=failed_count,
            optional_loaded_count=optional_loaded_count,
            checks=[check.__dict__ for check in checks],
            telemetry={
                "gate": self.name,
                "version": self.version,
                "read_only": True,
                "expected_required_adapters": len(EXPECTED_ADAPTERS),
                "optional_adapters_loaded": optional_loaded_count,
                "generated_at": _utc_now(),
            },
        )

    def _required_engine_ids(self) -> set:
        return {spec["engine_id"] for spec in EXPECTED_ADAPTERS}

    def _check_adapter(self, spec: Dict[str, str], required: bool) -> GateCheck:
        try:
            module = import_module(spec["module"])
            adapter_class = getattr(module, spec["class_name"])
            adapter = self._build_adapter(adapter_class)

            engine_id = getattr(adapter, "engine_id", None)
            if engine_id != spec["engine_id"]:
                return GateCheck(
                    engine_id=spec["engine_id"],
                    module=spec["module"],
                    class_name=spec["class_name"],
                    status="fail" if required else "optional_missing",
                    error=f"engine_id mismatch: expected {spec['engine_id']}, got {engine_id}",
                )

            read_only = bool(getattr(adapter, "read_only", False))
            if not read_only:
                return GateCheck(
                    engine_id=spec["engine_id"],
                    module=spec["module"],
                    class_name=spec["class_name"],
                    status="fail" if required else "optional_missing",
                    read_only=False,
                    error="adapter is not read_only",
                )

            health = self._run_health(adapter)
            health_status = health.get("status") if isinstance(health, dict) else None

            result = self._run_analyze(adapter, spec["engine_id"])
            signals = getattr(result, "signals", [])
            if not isinstance(signals, list):
                signals = []

            predictions = self._run_predict(adapter, spec["engine_id"])
            if not isinstance(predictions, list):
                predictions = []

            if len(signals) < 1:
                return GateCheck(
                    engine_id=spec["engine_id"],
                    module=spec["module"],
                    class_name=spec["class_name"],
                    status="fail" if required else "optional_missing",
                    read_only=read_only,
                    health_status=health_status,
                    signal_count=len(signals),
                    prediction_count=len(predictions),
                    error="adapter did not produce canonical signals",
                )

            if len(predictions) < 1:
                return GateCheck(
                    engine_id=spec["engine_id"],
                    module=spec["module"],
                    class_name=spec["class_name"],
                    status="fail" if required else "optional_missing",
                    read_only=read_only,
                    health_status=health_status,
                    signal_count=len(signals),
                    prediction_count=len(predictions),
                    error="adapter did not produce canonical predictions",
                )

            return GateCheck(
                engine_id=spec["engine_id"],
                module=spec["module"],
                class_name=spec["class_name"],
                status="pass",
                read_only=read_only,
                health_status=health_status,
                signal_count=len(signals),
                prediction_count=len(predictions),
            )

        except Exception as exc:
            return GateCheck(
                engine_id=spec["engine_id"],
                module=spec["module"],
                class_name=spec["class_name"],
                status="fail" if required else "optional_missing",
                error=str(exc),
            )

    def _build_adapter(self, adapter_class: Any) -> Any:
        try:
            return adapter_class(runtime_paths=self.runtime_paths, engine=None)
        except TypeError:
            try:
                return adapter_class(runtime_paths=self.runtime_paths)
            except TypeError:
                try:
                    return adapter_class(engine=None)
                except TypeError:
                    return adapter_class()

    def _run_health(self, adapter: Any) -> Dict[str, Any]:
        health = getattr(adapter, "health", None)
        if callable(health):
            result = health()
            return result if isinstance(result, dict) else {"status": "unknown"}
        return {"status": "missing"}

    def _run_analyze(self, adapter: Any, engine_id: str) -> Any:
        payload = self._sample_payload(engine_id)
        analyze = getattr(adapter, "analyze", None)
        if callable(analyze):
            return analyze(payload)

        run = getattr(adapter, "run", None)
        if callable(run):
            return run(payload)

        raise AttributeError("adapter has no analyze or run method")

    def _run_predict(self, adapter: Any, engine_id: str) -> List[Any]:
        payload = self._sample_payload(engine_id)
        predict = getattr(adapter, "predict", None)
        if callable(predict):
            return predict(payload)
        return []

    def _sample_payload(self, engine_id: str) -> Dict[str, Any]:
        base = {
            "market_id": f"OEM010-{engine_id.upper().replace('.', '-')}-YES",
            "confidence": 0.81,
            "edge": 0.37,
            "score": 0.37,
        }

        if engine_id == "oracle.market_relationship":
            base.update({"related_market_id": "OEM010-RELATED", "relationship_score": 0.37})
        elif engine_id == "oracle.market_influence":
            base.update({"influence_source": "integration_gate", "influence_score": 0.37})
        elif engine_id == "oracle.market_sentiment":
            base.update({"sentiment_source": "integration_gate", "sentiment_score": 0.37})
        elif engine_id == "oracle.discovery":
            base.update({"discovery_source": "integration_gate", "discovery_type": "gate_probe", "discovery_score": 0.37})
        elif engine_id == "oracle.recall_ledger":
            base.update({"ledger_key": "gate_pattern", "recall_score": 0.37, "sample_size": 12})
        elif engine_id == "oracle.query_audit":
            base.update({"query_id": "gate_query", "audit_score": 0.37, "audit_status": "passed"})
        elif engine_id == "oracle.query_resolver":
            base.update({"query": "integration gate query", "resolved_market_id": base["market_id"], "resolver_score": 0.37})
        elif engine_id == "oracle.historical_pattern_recognition":
            base.update({"pattern_id": "gate_pattern", "pattern_score": 0.37})
        elif engine_id == "oracle.historical_outcome_tracking":
            base.update({"outcome_score": 0.37, "sample_size": 12})

        return base


def run_gate(runtime_paths: Optional[Any] = None) -> GateResult:
    return OracleEngineMigrationIntegrationGate(runtime_paths=runtime_paths).run()


__all__ = [
    "GATE_ID",
    "GATE_NAME",
    "GATE_VERSION",
    "EXPECTED_ADAPTERS",
    "OPTIONAL_ADAPTERS",
    "GateCheck",
    "GateResult",
    "OracleEngineMigrationIntegrationGate",
    "run_gate",
]
