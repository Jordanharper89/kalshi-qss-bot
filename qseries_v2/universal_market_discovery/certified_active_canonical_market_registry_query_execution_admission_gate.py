from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_active_canonical_market_registry_query_execution_engine import (
    CertifiedActiveMarketQueryExecution,
    ReadOnlyActiveMarketQueryExecutionLedger,
)

UMD_025_BUILD_ID = "UMD-025"
UMD_025_BUILD_NAME = (
    "Certified Active Canonical Market Registry "
    "Query Execution Admission Gate"
)
UMD_025_REVISION = (
    "UMD_025_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_"
    "QUERY_EXECUTION_ADMISSION_GATE_V1"
)
UMD_025_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_execution_commit",
    "execution_persistence",
    "execution_ledger_mutation",
    "active_registry_mutation",
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


@dataclass(frozen=True, slots=True)
class CertifiedActiveMarketQueryExecutionAdmissionDecision:
    execution_id: str
    execution_hash: str
    query_id: str
    result_id: str
    admitted: bool
    checks: Mapping[str, bool]
    rejection_reasons: Tuple[str, ...]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        execution_id = _text(
            self.execution_id,
            "execution_id",
        )
        if not execution_id.startswith(
            "umd:market-query-execution:"
        ):
            raise ValueError(
                "execution_id must use UMD execution prefix"
            )
        object.__setattr__(
            self,
            "execution_id",
            execution_id,
        )

        object.__setattr__(
            self,
            "execution_hash",
            _sha256(
                self.execution_hash,
                "execution_hash",
            ),
        )

        query_id = _text(
            self.query_id,
            "query_id",
        )
        if not query_id.startswith(
            "umd:market-query:"
        ):
            raise ValueError(
                "query_id must use UMD query prefix"
            )
        object.__setattr__(
            self,
            "query_id",
            query_id,
        )

        result_id = _text(
            self.result_id,
            "result_id",
        )
        if not result_id.startswith(
            "umd:market-query-result:"
        ):
            raise ValueError(
                "result_id must use UMD query-result prefix"
            )
        object.__setattr__(
            self,
            "result_id",
            result_id,
        )

        normalized_checks = {
            _text(str(name), "check name"): bool(passed)
            for name, passed in self.checks.items()
        }
        object.__setattr__(
            self,
            "checks",
            MappingProxyType(
                dict(sorted(normalized_checks.items()))
            ),
        )

        failed_checks = tuple(
            name
            for name, passed in self.checks.items()
            if not passed
        )
        reasons = tuple(
            sorted(
                {
                    _text(reason, "rejection reason")
                    for reason in self.rejection_reasons
                }
            )
        )
        object.__setattr__(
            self,
            "rejection_reasons",
            reasons,
        )

        if self.admitted:
            if failed_checks or reasons:
                raise ValueError(
                    "admitted decision cannot contain failures"
                )
        else:
            if not failed_checks:
                raise ValueError(
                    "rejected decision requires failed checks"
                )
            if reasons != tuple(sorted(failed_checks)):
                raise ValueError(
                    "rejection reasons must match failed checks"
                )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError(
                "execution-admission lineage must belong to UMD"
            )
        if self.lineage.build_id != UMD_025_BUILD_ID:
            raise ValueError(
                "execution-admission lineage must use build_id UMD-025"
            )
        if self.execution_hash not in self.lineage.parent_hashes:
            raise ValueError(
                "execution-admission lineage must include execution hash"
            )

    @property
    def decision_id(self) -> str:
        return "umd:market-query-execution-admission:" + deterministic_sha256(
            {
                "execution_id": self.execution_id,
                "execution_hash": self.execution_hash,
                "query_id": self.query_id,
                "result_id": self.result_id,
                "admitted": self.admitted,
                "checks": self.checks,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "decision_id": self.decision_id,
            "execution_id": self.execution_id,
            "execution_hash": self.execution_hash,
            "query_id": self.query_id,
            "result_id": self.result_id,
            "admitted": self.admitted,
            "checks": self.checks,
            "rejection_reasons": self.rejection_reasons,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def evaluate_active_market_query_execution(
    execution: CertifiedActiveMarketQueryExecution,
    existing_ledger: ReadOnlyActiveMarketQueryExecutionLedger,
    *,
    lineage: ImmutableLineage,
) -> CertifiedActiveMarketQueryExecutionAdmissionDecision:
    latest = existing_ledger.latest()

    checks = {
        "execution_id_not_seen": (
            existing_ledger.get(execution.execution_id) is None
        ),
        "execution_hash_not_seen": all(
            prior.execution_hash != execution.execution_hash
            for prior in existing_ledger.executions
        ),
        "result_id_not_seen": (
            existing_ledger.get_by_result(
                execution.result.result_id
            )
            is None
        ),
        "query_identity_bound": (
            execution.result.query.query_id
            == execution.request.query_id
        ),
        "result_identity_bound": (
            execution.result.result_id
            == "umd:market-query-result:"
            + deterministic_sha256(
                {
                    "query_id": execution.request.query_id,
                    "active_snapshot_id": (
                        execution.result.active_snapshot_id
                    ),
                    "active_snapshot_hash": (
                        execution.result.active_snapshot_hash
                    ),
                    "read_model_hash": (
                        execution.result.read_model_hash
                    ),
                    "market_record_hashes": tuple(
                        market.record_hash
                        for market in execution.result.markets
                    ),
                }
            )
        ),
        "execution_sequence_valid": (
            execution.execution_sequence == 1
            if latest is None
            else (
                execution.execution_sequence
                == latest.execution_sequence + 1
            )
        ),
        "previous_execution_hash_valid": (
            execution.previous_execution_hash is None
            if latest is None
            else (
                execution.previous_execution_hash
                == latest.execution_hash
            )
        ),
        "execution_hash_deterministic": (
            execution.execution_hash
            == deterministic_sha256(
                execution.to_canonical_dict()
            )
        ),
        "result_hash_deterministic": (
            execution.result.result_hash
            == deterministic_sha256(
                execution.result.to_canonical_dict()
            )
        ),
        "market_order_deterministic": tuple(
            market.canonical_market_id
            for market in execution.result.markets
        )
        == tuple(
            sorted(
                market.canonical_market_id
                for market in execution.result.markets
            )
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    return CertifiedActiveMarketQueryExecutionAdmissionDecision(
        execution_id=execution.execution_id,
        execution_hash=execution.execution_hash,
        query_id=execution.request.query_id,
        result_id=execution.result.result_id,
        admitted=not failed,
        checks=checks,
        rejection_reasons=failed,
        lineage=lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD025CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    gate_mode: str
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
            "gate_mode": self.gate_mode,
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


def build_umd_025_certification_manifest() -> UMD025CertificationManifest:
    return UMD025CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_025_BUILD_ID,
        build_name=UMD_025_BUILD_NAME,
        revision=UMD_025_REVISION,
        schema_version=UMD_025_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 25)
        ),
        gate_mode="read_only_execution_validation",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_025_foundation() -> Mapping[str, Any]:
    manifest = build_umd_025_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-025"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 25)
            )
        ),
        "read_only_execution_validation": (
            manifest.gate_mode
            == "read_only_execution_validation"
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


def verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate() -> bool:
    result = certify_umd_025_foundation()

    if not result["certified"]:
        raise RuntimeError(
            "UMD-025 certification failed: "
            + ", ".join(result["failed_checks"])
        )

    return True


__all__ = [
    "UMD_025_BUILD_ID",
    "UMD_025_BUILD_NAME",
    "UMD_025_REVISION",
    "UMD_025_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedActiveMarketQueryExecutionAdmissionDecision",
    "evaluate_active_market_query_execution",
    "UMD025CertificationManifest",
    "build_umd_025_certification_manifest",
    "certify_umd_025_foundation",
    "verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate",
]
