"""
OEM-011 Oracle Engine Migration Registry Bridge

Canonical registry bridge for migrated Oracle Engine Migration adapters.

Oracle remains read-only.
Q Series remains execution-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib import import_module
from typing import Any, Dict, List, Optional


BRIDGE_ID = "oracle.engine_migration.registry_bridge"
BRIDGE_NAME = "Oracle Engine Migration Registry Bridge"
BRIDGE_VERSION = "OEM-011"


MIGRATED_ENGINE_SPECS = [
    {
        "engine_id": "oracle.market_relationship",
        "module": "qseries_v2.integration.oem_003_market_relationship_engine_adapter",
        "class_name": "MarketRelationshipEngineAdapter",
        "builder_name": "build_engine",
        "adapter_group": "oem",
        "migration_id": "OEM-003",
    },
    {
        "engine_id": "oracle.market_influence",
        "module": "qseries_v2.integration.oem_004_market_influence_engine_adapter",
        "class_name": "MarketInfluenceEngineAdapter",
        "builder_name": "build_engine",
        "adapter_group": "oem",
        "migration_id": "OEM-004",
    },
    {
        "engine_id": "oracle.market_sentiment",
        "module": "qseries_v2.integration.oem_005_market_sentiment_engine_adapter",
        "class_name": "MarketSentimentEngineAdapter",
        "builder_name": "build_engine",
        "adapter_group": "oem",
        "migration_id": "OEM-005",
    },
    {
        "engine_id": "oracle.discovery",
        "module": "qseries_v2.integration.oem_006_discovery_engine_adapter",
        "class_name": "DiscoveryEngineAdapter",
        "builder_name": "build_engine",
        "adapter_group": "oem",
        "migration_id": "OEM-006",
    },
    {
        "engine_id": "oracle.recall_ledger",
        "module": "qseries_v2.integration.oem_007_recall_ledger_engine_adapter",
        "class_name": "RecallLedgerEngineAdapter",
        "builder_name": "build_engine",
        "adapter_group": "oem",
        "migration_id": "OEM-007",
    },
    {
        "engine_id": "oracle.query_audit",
        "module": "qseries_v2.integration.oem_008_query_audit_engine_adapter",
        "class_name": "QueryAuditEngineAdapter",
        "builder_name": "build_engine",
        "adapter_group": "oem",
        "migration_id": "OEM-008",
    },
    {
        "engine_id": "oracle.query_resolver",
        "module": "qseries_v2.integration.oem_009_query_resolver_engine_adapter",
        "class_name": "QueryResolverEngineAdapter",
        "builder_name": "build_engine",
        "adapter_group": "oem",
        "migration_id": "OEM-009",
    },
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RegistryBridgeEntry:
    engine_id: str
    module: str
    class_name: str
    migration_id: str
    status: str
    read_only: bool
    registered: bool = False
    health_status: Optional[str] = None
    error: Optional[str] = None
    registered_at: Optional[str] = None


@dataclass
class RegistryBridgeResult:
    bridge_id: str
    status: str
    total_specs: int
    loaded_count: int
    registered_count: int
    failed_count: int
    entries: List[Dict[str, Any]]
    telemetry: Dict[str, Any]
    generated_at: str = field(default_factory=_utc_now)


class OracleEngineMigrationRegistryBridge:
    bridge_id = BRIDGE_ID
    name = BRIDGE_NAME
    version = BRIDGE_VERSION
    read_only = True

    def __init__(self, runtime_paths: Optional[Any] = None):
        self.runtime_paths = runtime_paths

    def list_specs(self) -> List[Dict[str, Any]]:
        return [dict(spec) for spec in MIGRATED_ENGINE_SPECS]

    def build_all(self) -> List[Any]:
        engines = []
        for spec in MIGRATED_ENGINE_SPECS:
            engines.append(self._build_engine(spec))
        return engines

    def register_all(self, runtime: Any) -> RegistryBridgeResult:
        entries: List[RegistryBridgeEntry] = []

        for spec in MIGRATED_ENGINE_SPECS:
            entries.append(self._register_one(runtime, spec))

        loaded_count = sum(1 for entry in entries if entry.status in {"loaded", "registered"})
        registered_count = sum(1 for entry in entries if entry.registered)
        failed_count = sum(1 for entry in entries if entry.status == "failed")
        status = "pass" if failed_count == 0 and registered_count == len(MIGRATED_ENGINE_SPECS) else "fail"

        return RegistryBridgeResult(
            bridge_id=self.bridge_id,
            status=status,
            total_specs=len(MIGRATED_ENGINE_SPECS),
            loaded_count=loaded_count,
            registered_count=registered_count,
            failed_count=failed_count,
            entries=[entry.__dict__ for entry in entries],
            telemetry={
                "bridge": self.name,
                "version": self.version,
                "read_only": True,
                "spec_count": len(MIGRATED_ENGINE_SPECS),
                "generated_at": _utc_now(),
            },
        )

    def _register_one(self, runtime: Any, spec: Dict[str, Any]) -> RegistryBridgeEntry:
        try:
            engine = self._build_engine(spec)

            engine_id = getattr(engine, "engine_id", None)
            if engine_id != spec["engine_id"]:
                return RegistryBridgeEntry(
                    engine_id=spec["engine_id"],
                    module=spec["module"],
                    class_name=spec["class_name"],
                    migration_id=spec["migration_id"],
                    status="failed",
                    read_only=False,
                    error=f"engine_id mismatch: expected {spec['engine_id']}, got {engine_id}",
                )

            read_only = bool(getattr(engine, "read_only", False))
            if not read_only:
                return RegistryBridgeEntry(
                    engine_id=spec["engine_id"],
                    module=spec["module"],
                    class_name=spec["class_name"],
                    migration_id=spec["migration_id"],
                    status="failed",
                    read_only=False,
                    error="engine is not read_only",
                )

            health_status = None
            health = getattr(engine, "health", None)
            if callable(health):
                health_result = health()
                if isinstance(health_result, dict):
                    health_status = health_result.get("status")

            self._register_engine(runtime, engine)

            return RegistryBridgeEntry(
                engine_id=spec["engine_id"],
                module=spec["module"],
                class_name=spec["class_name"],
                migration_id=spec["migration_id"],
                status="registered",
                read_only=True,
                registered=True,
                health_status=health_status,
                registered_at=_utc_now(),
            )

        except Exception as exc:
            return RegistryBridgeEntry(
                engine_id=spec["engine_id"],
                module=spec["module"],
                class_name=spec["class_name"],
                migration_id=spec["migration_id"],
                status="failed",
                read_only=False,
                error=str(exc),
            )

    def _build_engine(self, spec: Dict[str, Any]) -> Any:
        module = import_module(spec["module"])

        builder = getattr(module, spec.get("builder_name", "build_engine"), None)
        if callable(builder):
            try:
                return builder(runtime_paths=self.runtime_paths)
            except TypeError:
                return builder()

        cls = getattr(module, spec["class_name"])
        try:
            return cls(runtime_paths=self.runtime_paths, engine=None)
        except TypeError:
            try:
                return cls(runtime_paths=self.runtime_paths)
            except TypeError:
                try:
                    return cls(engine=None)
                except TypeError:
                    return cls()

    def _register_engine(self, runtime: Any, engine: Any) -> None:
        for method_name in ("register_engine", "register", "add_engine"):
            method = getattr(runtime, method_name, None)
            if callable(method):
                method(engine)
                return

        registry = getattr(runtime, "registry", None)
        if registry is not None:
            for method_name in ("register_engine", "register", "add_engine"):
                method = getattr(registry, method_name, None)
                if callable(method):
                    method(engine)
                    return

        engines = getattr(runtime, "engines", None)
        if isinstance(engines, dict):
            engines[getattr(engine, "engine_id")] = engine
            return

        raise AttributeError("runtime does not expose a supported registration surface")


def build_bridge(runtime_paths: Optional[Any] = None) -> OracleEngineMigrationRegistryBridge:
    return OracleEngineMigrationRegistryBridge(runtime_paths=runtime_paths)


def register_migrated_oracle_engines(runtime: Any, runtime_paths: Optional[Any] = None) -> RegistryBridgeResult:
    return build_bridge(runtime_paths=runtime_paths).register_all(runtime)


__all__ = [
    "BRIDGE_ID",
    "BRIDGE_NAME",
    "BRIDGE_VERSION",
    "MIGRATED_ENGINE_SPECS",
    "RegistryBridgeEntry",
    "RegistryBridgeResult",
    "OracleEngineMigrationRegistryBridge",
    "build_bridge",
    "register_migrated_oracle_engines",
]
