from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_active_canonical_market_registry_read_model import (
    CertifiedActiveCanonicalMarketRegistryReadModel,
)
from .certified_active_canonical_market_registry_query_contract import (
    CertifiedActiveMarketQueryRequest,
    CertifiedActiveMarketQueryResult,
    execute_active_market_query,
)

UMD_024_BUILD_ID = "UMD-024"
UMD_024_BUILD_NAME = (
    "Certified Active Canonical Market Registry Query Execution Engine"
)
UMD_024_REVISION = (
    "UMD_024_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_"
    "QUERY_EXECUTION_ENGINE_V1"
)
UMD_024_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "registry_mutation",
    "snapshot_activation",
    "persistence_write",
    "oracle_memory_mutation",
    "publication",
    "order_submission",
    "trade_execution",
)


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _sha256(value: str, field_name: str) -> str:
    normalized = _text(value, field_name).lower()
    if len(normalized) != 64:
        raise ValueError(
            f"{field_name} must contain 64 hexadecimal characters"
        )
    if any(
        character not in "0123456789abcdef"
        for character in normalized
    ):
        raise ValueError(
            f"{field_name} must be lowercase SHA-256 hexadecimal"
        )
    return normalized


def _utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(
        dict(sorted((str(key), item) for key, item in value.items()))
    )


@dataclass(frozen=True, slots=True)
class CertifiedActiveMarketQueryExecution:
    execution_sequence: int
    previous_execution_hash: str | None
    request: CertifiedActiveMarketQueryRequest
    result: CertifiedActiveMarketQueryResult
    executed_at: datetime
    execution_context: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        if not isinstance(self.execution_sequence, int):
            raise TypeError("execution_sequence must be an integer")
        if self.execution_sequence < 1:
            raise ValueError("execution_sequence must be positive")

        if self.previous_execution_hash is None:
            if self.execution_sequence != 1:
                raise ValueError(
                    "only the first execution may omit previous_execution_hash"
                )
        else:
            object.__setattr__(
                self,
                "previous_execution_hash",
                _sha256(
                    self.previous_execution_hash,
                    "previous_execution_hash",
                ),
            )

        if self.result.query.query_id != self.request.query_id:
            raise ValueError(
                "result query does not match execution request"
            )

        object.__setattr__(
            self,
            "executed_at",
            _utc(self.executed_at, "executed_at"),
        )
        object.__setattr__(
            self,
            "execution_context",
            _freeze(self.execution_context),
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("execution lineage must belong to UMD")
        if self.lineage.build_id != UMD_024_BUILD_ID:
            raise ValueError(
                "execution lineage must use build_id UMD-024"
            )

        required_parents = {
            self.result.result_hash,
            self.result.read_model_hash,
        }
        if self.previous_execution_hash is not None:
            required_parents.add(self.previous_execution_hash)

        if not required_parents.issubset(
            set(self.lineage.parent_hashes)
        ):
            raise ValueError(
                "execution lineage is missing required parent hashes"
            )

    @property
    def execution_id(self) -> str:
        return "umd:market-query-execution:" + deterministic_sha256(
            {
                "execution_sequence": self.execution_sequence,
                "previous_execution_hash": self.previous_execution_hash,
                "query_id": self.request.query_id,
                "result_id": self.result.result_id,
                "active_snapshot_id": self.result.active_snapshot_id,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "execution_id": self.execution_id,
            "execution_sequence": self.execution_sequence,
            "previous_execution_hash": self.previous_execution_hash,
            "request": self.request,
            "result": self.result,
            "executed_at": self.executed_at,
            "execution_context": self.execution_context,
            "lineage": self.lineage,
        }

    @property
    def execution_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )

    def summary(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "execution_id": self.execution_id,
                "query_id": self.request.query_id,
                "query_mode": self.request.query_mode.value,
                "active_snapshot_id": self.result.active_snapshot_id,
                "active_snapshot_hash": self.result.active_snapshot_hash,
                "market_count": len(self.result.markets),
                "market_ids": tuple(
                    market.canonical_market_id
                    for market in self.result.markets
                ),
                "result_hash": self.result.result_hash,
                "execution_hash": self.execution_hash,
            }
        )


@dataclass(frozen=True, slots=True)
class ReadOnlyActiveMarketQueryExecutionLedger:
    executions: Tuple[CertifiedActiveMarketQueryExecution, ...]
    ledger_lineage: ImmutableLineage
    _by_execution_id: Mapping[
        str,
        CertifiedActiveMarketQueryExecution,
    ] = field(init=False, repr=False)
    _by_query_id: Mapping[
        str,
        Tuple[CertifiedActiveMarketQueryExecution, ...],
    ] = field(init=False, repr=False)
    _by_result_id: Mapping[
        str,
        CertifiedActiveMarketQueryExecution,
    ] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        ordered = tuple(
            sorted(
                self.executions,
                key=lambda execution: execution.execution_sequence,
            )
        )
        object.__setattr__(self, "executions", ordered)

        if self.ledger_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("execution-ledger lineage must belong to UMD")
        if self.ledger_lineage.build_id != UMD_024_BUILD_ID:
            raise ValueError(
                "execution-ledger lineage must use build_id UMD-024"
            )

        by_execution_id = {}
        by_query_id = {}
        by_result_id = {}
        previous_execution = None

        for expected_sequence, execution in enumerate(
            ordered,
            start=1,
        ):
            if execution.execution_sequence != expected_sequence:
                raise ValueError(
                    "execution sequence must be contiguous and start at 1"
                )

            if previous_execution is None:
                if execution.previous_execution_hash is not None:
                    raise ValueError(
                        "first execution must not have previous hash"
                    )
            else:
                if (
                    execution.previous_execution_hash
                    != previous_execution.execution_hash
                ):
                    raise ValueError(
                        "previous-execution hash chain mismatch"
                    )

            if execution.execution_id in by_execution_id:
                raise ValueError("duplicate execution ID")
            if execution.result.result_id in by_result_id:
                raise ValueError(
                    "query result may be executed only once"
                )

            by_execution_id[execution.execution_id] = execution
            by_result_id[execution.result.result_id] = execution
            by_query_id.setdefault(
                execution.request.query_id,
                [],
            ).append(execution)

            previous_execution = execution

        object.__setattr__(
            self,
            "_by_execution_id",
            MappingProxyType(by_execution_id),
        )
        object.__setattr__(
            self,
            "_by_query_id",
            MappingProxyType(
                {
                    query_id: tuple(values)
                    for query_id, values in by_query_id.items()
                }
            ),
        )
        object.__setattr__(
            self,
            "_by_result_id",
            MappingProxyType(by_result_id),
        )

    def get(
        self,
        execution_id: str,
    ) -> CertifiedActiveMarketQueryExecution | None:
        return self._by_execution_id.get(
            _text(execution_id, "execution_id")
        )

    def by_query(
        self,
        query_id: str,
    ) -> Tuple[CertifiedActiveMarketQueryExecution, ...]:
        return self._by_query_id.get(
            _text(query_id, "query_id"),
            (),
        )

    def get_by_result(
        self,
        result_id: str,
    ) -> CertifiedActiveMarketQueryExecution | None:
        return self._by_result_id.get(
            _text(result_id, "result_id")
        )

    def latest(
        self,
    ) -> CertifiedActiveMarketQueryExecution | None:
        if not self.executions:
            return None
        return self.executions[-1]

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "ledger_mode": "append_only_read_only",
            "executions": self.executions,
            "ledger_lineage": self.ledger_lineage,
        }

    @property
    def ledger_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def execute_certified_active_market_query(
    request: CertifiedActiveMarketQueryRequest,
    read_model: CertifiedActiveCanonicalMarketRegistryReadModel,
    *,
    execution_sequence: int,
    previous_execution_hash: str | None,
    executed_at: datetime,
    execution_context: Mapping[str, Any],
    result_lineage: ImmutableLineage,
    execution_lineage: ImmutableLineage,
) -> CertifiedActiveMarketQueryExecution:
    result = execute_active_market_query(
        request,
        read_model,
        lineage=result_lineage,
    )

    return CertifiedActiveMarketQueryExecution(
        execution_sequence=execution_sequence,
        previous_execution_hash=previous_execution_hash,
        request=request,
        result=result,
        executed_at=executed_at,
        execution_context=execution_context,
        lineage=execution_lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD024CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    engine_mode: str
    prohibited_capabilities: Tuple[str, ...]
    network_enabled: bool
    persistence_enabled: bool
    mutation_enabled: bool
    publication_enabled: bool
    execution_enabled: bool

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "subsystem_id": self.subsystem_id,
            "build_id": self.build_id,
            "build_name": self.build_name,
            "revision": self.revision,
            "schema_version": self.schema_version,
            "upstream_builds": self.upstream_builds,
            "engine_mode": self.engine_mode,
            "prohibited_capabilities": self.prohibited_capabilities,
            "network_enabled": self.network_enabled,
            "persistence_enabled": self.persistence_enabled,
            "mutation_enabled": self.mutation_enabled,
            "publication_enabled": self.publication_enabled,
            "execution_enabled": self.execution_enabled,
        }

    @property
    def manifest_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def build_umd_024_certification_manifest() -> UMD024CertificationManifest:
    return UMD024CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_024_BUILD_ID,
        build_name=UMD_024_BUILD_NAME,
        revision=UMD_024_REVISION,
        schema_version=UMD_024_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 24)
        ),
        engine_mode="deterministic_read_only_execution",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_active_market_query_execution_ledger(
    ledger: ReadOnlyActiveMarketQueryExecutionLedger,
) -> Mapping[str, Any]:
    checks = {
        "execution_ids_unique": len(
            {
                execution.execution_id
                for execution in ledger.executions
            }
        )
        == len(ledger.executions),
        "result_ids_unique": len(
            {
                execution.result.result_id
                for execution in ledger.executions
            }
        )
        == len(ledger.executions),
        "sequence_contiguous": tuple(
            execution.execution_sequence
            for execution in ledger.executions
        )
        == tuple(range(1, len(ledger.executions) + 1)),
        "deterministic_replay": (
            ledger.ledger_hash
            == deterministic_sha256(
                ledger.to_canonical_dict()
            )
        ),
        "read_only_indexes": (
            isinstance(
                ledger._by_execution_id,
                MappingProxyType,
            )
            and isinstance(
                ledger._by_query_id,
                MappingProxyType,
            )
            and isinstance(
                ledger._by_result_id,
                MappingProxyType,
            )
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    latest = ledger.latest()

    return MappingProxyType(
        {
            "certified": not failed,
            "ledger_hash": ledger.ledger_hash,
            "execution_count": len(ledger.executions),
            "latest_execution_id": (
                None
                if latest is None
                else latest.execution_id
            ),
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_024_foundation() -> Mapping[str, Any]:
    manifest = build_umd_024_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-024"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 24)
            )
        ),
        "deterministic_read_only_execution": (
            manifest.engine_mode
            == "deterministic_read_only_execution"
        ),
        "network_disabled": (
            manifest.network_enabled is False
        ),
        "persistence_disabled": (
            manifest.persistence_enabled is False
        ),
        "mutation_disabled": (
            manifest.mutation_enabled is False
        ),
        "publication_disabled": (
            manifest.publication_enabled is False
        ),
        "execution_disabled": (
            manifest.execution_enabled is False
        ),
        "deterministic_manifest_hash": (
            manifest.manifest_hash
            == deterministic_sha256(
                manifest.to_canonical_dict()
            )
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    return MappingProxyType(
        {
            "certified": not failed,
            "build_id": manifest.build_id,
            "revision": manifest.revision,
            "manifest_hash": manifest.manifest_hash,
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def verify_umd_024_certified_active_canonical_market_registry_query_execution_engine() -> bool:
    result = certify_umd_024_foundation()

    if not result["certified"]:
        raise RuntimeError(
            "UMD-024 certification failed: "
            + ", ".join(result["failed_checks"])
        )

    return True


__all__ = [
    "UMD_024_BUILD_ID",
    "UMD_024_BUILD_NAME",
    "UMD_024_REVISION",
    "UMD_024_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedActiveMarketQueryExecution",
    "ReadOnlyActiveMarketQueryExecutionLedger",
    "execute_certified_active_market_query",
    "UMD024CertificationManifest",
    "build_umd_024_certification_manifest",
    "certify_active_market_query_execution_ledger",
    "certify_umd_024_foundation",
    "verify_umd_024_certified_active_canonical_market_registry_query_execution_engine",
]
