from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_canonical_market_contract import CertifiedCanonicalMarket
from .certified_canonical_market_registry_snapshot_activation_contract import (
    ReadOnlyActiveCanonicalMarketRegistry,
)
from .certified_canonical_market_registry_snapshot_activation_ledger import (
    ReadOnlySnapshotActivationLedger,
)

UMD_022_BUILD_ID = "UMD-022"
UMD_022_BUILD_NAME = "Certified Active Canonical Market Registry Read Model"
UMD_022_REVISION = (
    "UMD_022_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_READ_MODEL_V1"
)
UMD_022_SCHEMA_VERSION = "1.0.0"

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


def _value_text(value: Any) -> str:
    raw = getattr(value, "value", value)
    return str(raw).strip().lower()


@dataclass(frozen=True, slots=True)
class CertifiedActiveCanonicalMarketRegistryReadModel:
    active_registry: ReadOnlyActiveCanonicalMarketRegistry
    activation_ledger: ReadOnlySnapshotActivationLedger
    lineage: ImmutableLineage
    _by_market_id: Mapping[str, CertifiedCanonicalMarket] = field(
        init=False,
        repr=False,
    )
    _by_venue_id: Mapping[str, Tuple[CertifiedCanonicalMarket, ...]] = field(
        init=False,
        repr=False,
    )
    _by_category_id: Mapping[str, Tuple[CertifiedCanonicalMarket, ...]] = field(
        init=False,
        repr=False,
    )
    _by_lifecycle: Mapping[str, Tuple[CertifiedCanonicalMarket, ...]] = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("read-model lineage must belong to UMD")
        if self.lineage.build_id != UMD_022_BUILD_ID:
            raise ValueError(
                "read-model lineage must use build_id UMD-022"
            )

        activation = self.active_registry.activation
        latest_admitted = self.activation_ledger.latest_admitted()

        if latest_admitted is None:
            raise ValueError(
                "active registry requires an admitted activation ledger entry"
            )

        if (
            latest_admitted.decision.activation_id
            != activation.activation_id
        ):
            raise ValueError(
                "active registry activation does not match latest admitted ledger entry"
            )
        if (
            latest_admitted.decision.activation_hash
            != activation.activation_hash
        ):
            raise ValueError(
                "active registry activation hash does not match ledger"
            )
        if (
            latest_admitted.decision.snapshot_id
            != self.active_registry.active_snapshot_id
        ):
            raise ValueError(
                "active snapshot ID does not match activation ledger"
            )
        if (
            latest_admitted.decision.snapshot_hash
            != self.active_registry.active_snapshot_hash
        ):
            raise ValueError(
                "active snapshot hash does not match activation ledger"
            )

        required_parents = {
            self.active_registry.registry_hash,
            self.activation_ledger.ledger_hash,
            activation.activation_hash,
            latest_admitted.entry_hash,
        }
        if not required_parents.issubset(
            set(self.lineage.parent_hashes)
        ):
            raise ValueError(
                "read-model lineage is missing required parent hashes"
            )

        markets = tuple(
            sorted(
                self.active_registry.snapshot.markets,
                key=lambda market: market.canonical_market_id,
            )
        )

        by_market_id = {}
        by_venue_id = {}
        by_category_id = {}
        by_lifecycle = {}

        for market in markets:
            market_id = market.canonical_market_id
            if market_id in by_market_id:
                raise ValueError(
                    "duplicate canonical market ID in active registry"
                )
            by_market_id[market_id] = market

            venue_id = _text(
                market.venue.venue_id,
                "venue_id",
            ).lower()
            by_venue_id.setdefault(
                venue_id,
                [],
            ).append(market)

            category_id = _text(
                market.category.category_id,
                "category_id",
            ).lower()
            by_category_id.setdefault(
                category_id,
                [],
            ).append(market)

            lifecycle = _value_text(market.lifecycle)
            by_lifecycle.setdefault(
                lifecycle,
                [],
            ).append(market)

        object.__setattr__(
            self,
            "_by_market_id",
            MappingProxyType(by_market_id),
        )
        object.__setattr__(
            self,
            "_by_venue_id",
            MappingProxyType(
                {
                    key: tuple(
                        sorted(
                            values,
                            key=lambda market: market.canonical_market_id,
                        )
                    )
                    for key, values in by_venue_id.items()
                }
            ),
        )
        object.__setattr__(
            self,
            "_by_category_id",
            MappingProxyType(
                {
                    key: tuple(
                        sorted(
                            values,
                            key=lambda market: market.canonical_market_id,
                        )
                    )
                    for key, values in by_category_id.items()
                }
            ),
        )
        object.__setattr__(
            self,
            "_by_lifecycle",
            MappingProxyType(
                {
                    key: tuple(
                        sorted(
                            values,
                            key=lambda market: market.canonical_market_id,
                        )
                    )
                    for key, values in by_lifecycle.items()
                }
            ),
        )

    @property
    def active_snapshot_id(self) -> str:
        return self.active_registry.active_snapshot_id

    @property
    def active_snapshot_hash(self) -> str:
        return self.active_registry.active_snapshot_hash

    @property
    def market_count(self) -> int:
        return len(self._by_market_id)

    def get(
        self,
        canonical_market_id: str,
    ) -> CertifiedCanonicalMarket | None:
        return self._by_market_id.get(
            _text(
                canonical_market_id,
                "canonical_market_id",
            )
        )

    def by_venue(
        self,
        venue_id: str,
    ) -> Tuple[CertifiedCanonicalMarket, ...]:
        return self._by_venue_id.get(
            _text(venue_id, "venue_id").lower(),
            (),
        )

    def by_category(
        self,
        category_id: str,
    ) -> Tuple[CertifiedCanonicalMarket, ...]:
        return self._by_category_id.get(
            _text(category_id, "category_id").lower(),
            (),
        )

    def by_lifecycle(
        self,
        lifecycle: Any,
    ) -> Tuple[CertifiedCanonicalMarket, ...]:
        return self._by_lifecycle.get(
            _value_text(lifecycle),
            (),
        )

    def market_ids(
        self,
    ) -> Tuple[str, ...]:
        return tuple(sorted(self._by_market_id))

    def venue_ids(
        self,
    ) -> Tuple[str, ...]:
        return tuple(sorted(self._by_venue_id))

    def category_ids(
        self,
    ) -> Tuple[str, ...]:
        return tuple(sorted(self._by_category_id))

    def lifecycle_values(
        self,
    ) -> Tuple[str, ...]:
        return tuple(sorted(self._by_lifecycle))

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "read_model_mode": "active_snapshot_read_only",
            "active_snapshot_id": self.active_snapshot_id,
            "active_snapshot_hash": self.active_snapshot_hash,
            "active_registry_hash": self.active_registry.registry_hash,
            "activation_ledger_hash": self.activation_ledger.ledger_hash,
            "market_record_hashes": tuple(
                self._by_market_id[market_id].record_hash
                for market_id in self.market_ids()
            ),
            "venue_index": {
                venue_id: tuple(
                    market.canonical_market_id
                    for market in self._by_venue_id[venue_id]
                )
                for venue_id in self.venue_ids()
            },
            "category_index": {
                category_id: tuple(
                    market.canonical_market_id
                    for market in self._by_category_id[category_id]
                )
                for category_id in self.category_ids()
            },
            "lifecycle_index": {
                lifecycle: tuple(
                    market.canonical_market_id
                    for market in self._by_lifecycle[lifecycle]
                )
                for lifecycle in self.lifecycle_values()
            },
            "lineage": self.lineage,
        }

    @property
    def read_model_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class UMD022CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    read_model_mode: str
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
            "read_model_mode": self.read_model_mode,
            "prohibited_capabilities": self.prohibited_capabilities,
            "network_enabled": self.network_enabled,
            "persistence_enabled": self.persistence_enabled,
            "mutation_enabled": self.mutation_enabled,
            "publication_enabled": self.publication_enabled,
            "execution_enabled": self.execution_enabled,
        }

    @property
    def manifest_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


def build_umd_022_certification_manifest() -> UMD022CertificationManifest:
    return UMD022CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_022_BUILD_ID,
        build_name=UMD_022_BUILD_NAME,
        revision=UMD_022_REVISION,
        schema_version=UMD_022_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 22)
        ),
        read_model_mode="active_snapshot_read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_active_canonical_market_registry_read_model(
    read_model: CertifiedActiveCanonicalMarketRegistryReadModel,
) -> Mapping[str, Any]:
    checks = {
        "market_ids_unique": (
            len(read_model.market_ids())
            == read_model.market_count
        ),
        "market_order_deterministic": (
            read_model.market_ids()
            == tuple(sorted(read_model.market_ids()))
        ),
        "venue_order_deterministic": (
            read_model.venue_ids()
            == tuple(sorted(read_model.venue_ids()))
        ),
        "category_order_deterministic": (
            read_model.category_ids()
            == tuple(sorted(read_model.category_ids()))
        ),
        "lifecycle_order_deterministic": (
            read_model.lifecycle_values()
            == tuple(sorted(read_model.lifecycle_values()))
        ),
        "active_snapshot_bound": (
            read_model.active_snapshot_id
            == read_model.active_registry.active_snapshot_id
            and read_model.active_snapshot_hash
            == read_model.active_registry.active_snapshot_hash
        ),
        "deterministic_replay": (
            read_model.read_model_hash
            == deterministic_sha256(
                read_model.to_canonical_dict()
            )
        ),
        "read_only_indexes": (
            isinstance(
                read_model._by_market_id,
                MappingProxyType,
            )
            and isinstance(
                read_model._by_venue_id,
                MappingProxyType,
            )
            and isinstance(
                read_model._by_category_id,
                MappingProxyType,
            )
            and isinstance(
                read_model._by_lifecycle,
                MappingProxyType,
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
            "read_model_hash": read_model.read_model_hash,
            "active_snapshot_id": read_model.active_snapshot_id,
            "active_snapshot_hash": read_model.active_snapshot_hash,
            "market_count": read_model.market_count,
            "venue_count": len(read_model.venue_ids()),
            "category_count": len(read_model.category_ids()),
            "lifecycle_count": len(read_model.lifecycle_values()),
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_022_foundation() -> Mapping[str, Any]:
    manifest = build_umd_022_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-022"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 22)
            )
        ),
        "active_snapshot_read_only": (
            manifest.read_model_mode
            == "active_snapshot_read_only"
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


def verify_umd_022_certified_active_canonical_market_registry_read_model() -> bool:
    result = certify_umd_022_foundation()

    if not result["certified"]:
        raise RuntimeError(
            "UMD-022 certification failed: "
            + ", ".join(result["failed_checks"])
        )

    return True


__all__ = [
    "UMD_022_BUILD_ID",
    "UMD_022_BUILD_NAME",
    "UMD_022_REVISION",
    "UMD_022_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedActiveCanonicalMarketRegistryReadModel",
    "UMD022CertificationManifest",
    "build_umd_022_certification_manifest",
    "certify_active_canonical_market_registry_read_model",
    "certify_umd_022_foundation",
    "verify_umd_022_certified_active_canonical_market_registry_read_model",
]
