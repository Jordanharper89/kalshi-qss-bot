"""
OEM-015 Runtime Bootstrap Integration Gate

Validates the completed OEM migration runtime layer:

- OEM-011 Registry Bridge
- OEM-012 Migrated Engine Aggregator Gate
- OEM-014 Runtime Bootstrap Manager

Oracle remains read-only.
Q Series remains execution-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


GATE_ID = "oracle.engine_migration.runtime_bootstrap_gate"
GATE_NAME = "Runtime Bootstrap Integration Gate"
GATE_VERSION = "OEM-015"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class BootstrapGateCheck:
    check_id: str
    status: str
    details: Dict[str, Any]
    error: Optional[str] = None
    checked_at: str = field(default_factory=_utc_now)


@dataclass
class RuntimeBootstrapGateResult:
    gate_id: str
    status: str
    check_count: int
    passed_count: int
    failed_count: int
    checks: List[Dict[str, Any]]
    telemetry: Dict[str, Any]
    generated_at: str = field(default_factory=_utc_now)


class RuntimeBootstrapIntegrationGate:
    gate_id = GATE_ID
    name = GATE_NAME
    version = GATE_VERSION
    read_only = True

    def __init__(self, runtime_paths: Optional[Any] = None):
        self.runtime_paths = runtime_paths

    def run(self) -> RuntimeBootstrapGateResult:
        checks = [
            self._check_registry_bridge(),
            self._check_aggregator_gate(),
            self._check_bootstrap_manager(),
            self._check_duplicate_protection(),
            self._check_registered_prediction_readiness(),
        ]

        passed = sum(1 for item in checks if item.status == "pass")
        failed = sum(1 for item in checks if item.status == "fail")

        return RuntimeBootstrapGateResult(
            gate_id=self.gate_id,
            status="pass" if failed == 0 else "fail",
            check_count=len(checks),
            passed_count=passed,
            failed_count=failed,
            checks=[item.__dict__ for item in checks],
            telemetry={
                "gate": self.name,
                "version": self.version,
                "read_only": True,
                "checkpoint": "OEM runtime bootstrap layer",
                "generated_at": _utc_now(),
            },
        )

    def _check_registry_bridge(self) -> BootstrapGateCheck:
        try:
            from qseries_v2.integration.oem_011_oracle_engine_migration_registry_bridge import (
                MIGRATED_ENGINE_SPECS,
                OracleEngineMigrationRegistryBridge,
            )

            bridge = OracleEngineMigrationRegistryBridge(runtime_paths=self.runtime_paths)
            engines = bridge.build_all()

            engine_ids = {engine.engine_id for engine in engines}
            expected_ids = {spec["engine_id"] for spec in MIGRATED_ENGINE_SPECS}

            assert engine_ids == expected_ids
            assert all(getattr(engine, "read_only", False) is True for engine in engines)

            return BootstrapGateCheck(
                check_id="registry_bridge",
                status="pass",
                details={
                    "expected_engines": len(expected_ids),
                    "loaded_engines": len(engine_ids),
                    "read_only": True,
                },
            )

        except Exception as exc:
            return BootstrapGateCheck(
                check_id="registry_bridge",
                status="fail",
                details={},
                error=str(exc),
            )

    def _check_aggregator_gate(self) -> BootstrapGateCheck:
        try:
            from qseries_v2.integration.oem_012_migrated_engine_aggregator_gate import run_gate

            result = run_gate(runtime_paths=self.runtime_paths)

            assert result.status == "pass"
            assert result.engine_count == 7
            assert result.total_signals >= 7
            assert result.total_predictions >= 7

            return BootstrapGateCheck(
                check_id="migrated_engine_aggregator_gate",
                status="pass",
                details={
                    "engine_count": result.engine_count,
                    "total_signals": result.total_signals,
                    "total_predictions": result.total_predictions,
                    "read_only": result.telemetry.get("read_only"),
                },
            )

        except Exception as exc:
            return BootstrapGateCheck(
                check_id="migrated_engine_aggregator_gate",
                status="fail",
                details={},
                error=str(exc),
            )

    def _check_bootstrap_manager(self) -> BootstrapGateCheck:
        try:
            from qseries_v2.integration.oem_014_oracle_runtime_bootstrap_manager import bootstrap_oracle_runtime

            result = bootstrap_oracle_runtime(runtime_paths=self.runtime_paths)

            assert result.status == "pass"
            assert result.runtime_status == "ready"
            assert result.registered_engines == 7
            assert result.healthy_engines == 7
            assert result.read_only is True

            return BootstrapGateCheck(
                check_id="runtime_bootstrap_manager",
                status="pass",
                details={
                    "runtime_status": result.runtime_status,
                    "registered_engines": result.registered_engines,
                    "healthy_engines": result.healthy_engines,
                    "signal_bus": result.signal_bus_status,
                    "aggregator": result.aggregator_status,
                    "read_only": result.read_only,
                },
            )

        except Exception as exc:
            return BootstrapGateCheck(
                check_id="runtime_bootstrap_manager",
                status="fail",
                details={},
                error=str(exc),
            )

    def _check_duplicate_protection(self) -> BootstrapGateCheck:
        try:
            from qseries_v2.integration.oem_014_oracle_runtime_bootstrap_manager import (
                BootstrapRuntimeSurface,
                bootstrap_oracle_runtime,
            )

            runtime = BootstrapRuntimeSurface()

            first = bootstrap_oracle_runtime(runtime=runtime, runtime_paths=self.runtime_paths)
            second = bootstrap_oracle_runtime(runtime=runtime, runtime_paths=self.runtime_paths)

            assert first.status == "pass"
            assert first.registered_engines == 7
            assert second.runtime_status == "degraded"
            assert second.duplicate_count == 7
            assert second.registered_engines == 0
            assert len(runtime.engines) == 7

            return BootstrapGateCheck(
                check_id="duplicate_protection",
                status="pass",
                details={
                    "first_registered": first.registered_engines,
                    "second_duplicates": second.duplicate_count,
                    "runtime_engines": len(runtime.engines),
                },
            )

        except Exception as exc:
            return BootstrapGateCheck(
                check_id="duplicate_protection",
                status="fail",
                details={},
                error=str(exc),
            )

    def _check_registered_prediction_readiness(self) -> BootstrapGateCheck:
        try:
            from qseries_v2.integration.oem_014_oracle_runtime_bootstrap_manager import (
                BootstrapRuntimeSurface,
                bootstrap_oracle_runtime,
            )

            runtime = BootstrapRuntimeSurface()
            report = bootstrap_oracle_runtime(runtime=runtime, runtime_paths=self.runtime_paths)

            assert report.status == "pass"
            assert len(runtime.engines) == 7

            prediction_count = 0

            for engine_id, engine in runtime.engines.items():
                predictions = engine.predict(
                    {
                        "market_id": f"OEM015-{engine_id.upper().replace('.', '-')}-YES",
                        "resolved_market_id": f"OEM015-{engine_id.upper().replace('.', '-')}-YES",
                        "related_market_id": "OEM015-RELATED",
                        "query": "OEM-015 readiness query",
                        "score": 0.46,
                        "edge": 0.46,
                        "confidence": 0.86,
                        "relationship_score": 0.46,
                        "influence_score": 0.46,
                        "sentiment_score": 0.46,
                        "discovery_score": 0.46,
                        "recall_score": 0.46,
                        "audit_score": 0.46,
                        "resolver_score": 0.46,
                    }
                )

                assert isinstance(predictions, list)
                assert len(predictions) >= 1
                assert getattr(engine, "read_only", False) is True
                prediction_count += len(predictions)

            return BootstrapGateCheck(
                check_id="registered_prediction_readiness",
                status="pass",
                details={
                    "runtime_engines": len(runtime.engines),
                    "prediction_count": prediction_count,
                    "read_only": True,
                },
            )

        except Exception as exc:
            return BootstrapGateCheck(
                check_id="registered_prediction_readiness",
                status="fail",
                details={},
                error=str(exc),
            )


def run_gate(runtime_paths: Optional[Any] = None) -> RuntimeBootstrapGateResult:
    return RuntimeBootstrapIntegrationGate(runtime_paths=runtime_paths).run()


__all__ = [
    "GATE_ID",
    "GATE_NAME",
    "GATE_VERSION",
    "BootstrapGateCheck",
    "RuntimeBootstrapGateResult",
    "RuntimeBootstrapIntegrationGate",
    "run_gate",
]
