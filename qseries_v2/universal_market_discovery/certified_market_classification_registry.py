from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    MarketInstrumentType,
    MarketLifecycle,
    SettlementMethod,
    deterministic_sha256,
)
from .certified_canonical_market_contract import (
    AssetClass,
    CertifiedCanonicalMarket,
    GeographicScope,
)
from .certified_market_category_hierarchy_registry import (
    ReadOnlyMarketCategoryHierarchyRegistry,
)

UMD_006_BUILD_ID = "UMD-006"
UMD_006_BUILD_NAME = "Certified Market Classification Registry"
UMD_006_REVISION = "UMD_006_CERTIFIED_MARKET_CLASSIFICATION_REGISTRY_V1"
UMD_006_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "venue_api_connection",
    "credential_loading",
    "automatic_ai_classification",
    "persistence_write",
    "registry_mutation",
    "oracle_memory_mutation",
    "publication",
    "order_submission",
    "trade_execution",
)

def _text(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized

def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(
        dict(sorted((str(key), item) for key, item in value.items()))
    )

@dataclass(frozen=True, slots=True)
class CertifiedMarketClassification:
    canonical_market_id: str
    category_id: str
    asset_class: AssetClass
    instrument_type: MarketInstrumentType
    geographic_scope: GeographicScope
    settlement_method: SettlementMethod
    lifecycle: MarketLifecycle
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        market_id = _text(self.canonical_market_id, "canonical_market_id")
        if not market_id.startswith("umd:mkt:"):
            raise ValueError("canonical_market_id must use the UMD market prefix")
        object.__setattr__(self, "canonical_market_id", market_id)

        object.__setattr__(
            self,
            "category_id",
            _text(self.category_id, "category_id").lower(),
        )

        if not isinstance(self.asset_class, AssetClass):
            object.__setattr__(
                self,
                "asset_class",
                AssetClass(self.asset_class),
            )
        if not isinstance(self.instrument_type, MarketInstrumentType):
            object.__setattr__(
                self,
                "instrument_type",
                MarketInstrumentType(self.instrument_type),
            )
        if not isinstance(self.geographic_scope, GeographicScope):
            object.__setattr__(
                self,
                "geographic_scope",
                GeographicScope(self.geographic_scope),
            )
        if not isinstance(self.settlement_method, SettlementMethod):
            object.__setattr__(
                self,
                "settlement_method",
                SettlementMethod(self.settlement_method),
            )
        if not isinstance(self.lifecycle, MarketLifecycle):
            object.__setattr__(
                self,
                "lifecycle",
                MarketLifecycle(self.lifecycle),
            )

        object.__setattr__(self, "metadata", _freeze(self.metadata))

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("classification lineage must belong to UMD")
        if self.lineage.build_id != UMD_006_BUILD_ID:
            raise ValueError("classification lineage must use build_id UMD-006")

    @classmethod
    def from_market(
        cls,
        market: CertifiedCanonicalMarket,
        *,
        metadata: Mapping[str, Any],
        lineage: ImmutableLineage,
    ) -> "CertifiedMarketClassification":
        return cls(
            canonical_market_id=market.canonical_market_id,
            category_id=market.category.category_id,
            asset_class=market.asset_class,
            instrument_type=market.instrument_type,
            geographic_scope=market.geographic_scope,
            settlement_method=market.settlement_method,
            lifecycle=market.lifecycle,
            metadata=metadata,
            lineage=lineage,
        )

    def identity_payload(self) -> Mapping[str, Any]:
        return {"canonical_market_id": self.canonical_market_id}

    @property
    def classification_id(self) -> str:
        return f"umd:classification:{deterministic_sha256(self.identity_payload())}"

    def classification_payload(self) -> Mapping[str, Any]:
        return {
            "category_id": self.category_id,
            "asset_class": self.asset_class,
            "instrument_type": self.instrument_type,
            "geographic_scope": self.geographic_scope,
            "settlement_method": self.settlement_method,
            "lifecycle": self.lifecycle,
        }

    @property
    def classification_fingerprint(self) -> str:
        return deterministic_sha256(self.classification_payload())

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "classification_id": self.classification_id,
            "canonical_market_id": self.canonical_market_id,
            "category_id": self.category_id,
            "asset_class": self.asset_class,
            "instrument_type": self.instrument_type,
            "geographic_scope": self.geographic_scope,
            "settlement_method": self.settlement_method,
            "lifecycle": self.lifecycle,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class ReadOnlyMarketClassificationRegistry:
    classifications: Tuple[CertifiedMarketClassification, ...]
    markets: Tuple[CertifiedCanonicalMarket, ...]
    category_registry: ReadOnlyMarketCategoryHierarchyRegistry
    registry_lineage: ImmutableLineage
    _by_market_id: Mapping[str, CertifiedMarketClassification] = field(
        init=False,
        repr=False,
    )
    _by_classification_id: Mapping[str, CertifiedMarketClassification] = field(
        init=False,
        repr=False,
    )
    _by_category_id: Mapping[str, Tuple[CertifiedMarketClassification, ...]] = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        ordered_classifications = tuple(
            sorted(
                self.classifications,
                key=lambda item: item.classification_id,
            )
        )
        ordered_markets = tuple(
            sorted(
                self.markets,
                key=lambda item: item.canonical_market_id,
            )
        )
        object.__setattr__(
            self,
            "classifications",
            ordered_classifications,
        )
        object.__setattr__(self, "markets", ordered_markets)

        if self.registry_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("registry lineage must belong to UMD")
        if self.registry_lineage.build_id != UMD_006_BUILD_ID:
            raise ValueError("registry lineage must use build_id UMD-006")

        market_by_id = {
            market.canonical_market_id: market
            for market in ordered_markets
        }
        if len(market_by_id) != len(ordered_markets):
            raise ValueError("duplicate canonical market IDs supplied")

        by_market_id = {}
        by_classification_id = {}
        category_groups = {}

        for classification in ordered_classifications:
            if classification.classification_id in by_classification_id:
                raise ValueError("duplicate classification ID")
            if classification.canonical_market_id in by_market_id:
                raise ValueError(
                    "canonical market may have only one certified classification"
                )

            market = market_by_id.get(classification.canonical_market_id)
            if market is None:
                raise ValueError(
                    f"unknown canonical market ID: "
                    f"{classification.canonical_market_id}"
                )

            self.category_registry.validate_market(market)

            expected = CertifiedMarketClassification.from_market(
                market,
                metadata=classification.metadata,
                lineage=classification.lineage,
            )

            if (
                classification.classification_payload()
                != expected.classification_payload()
            ):
                raise ValueError(
                    "classification fields do not match canonical market"
                )

            if self.category_registry.get(classification.category_id) is None:
                raise ValueError(
                    f"unregistered category: {classification.category_id}"
                )

            by_market_id[classification.canonical_market_id] = classification
            by_classification_id[
                classification.classification_id
            ] = classification
            category_groups.setdefault(
                classification.category_id,
                [],
            ).append(classification)

        frozen_groups = {
            category_id: tuple(
                sorted(
                    items,
                    key=lambda item: item.canonical_market_id,
                )
            )
            for category_id, items in category_groups.items()
        }

        object.__setattr__(
            self,
            "_by_market_id",
            MappingProxyType(by_market_id),
        )
        object.__setattr__(
            self,
            "_by_classification_id",
            MappingProxyType(by_classification_id),
        )
        object.__setattr__(
            self,
            "_by_category_id",
            MappingProxyType(frozen_groups),
        )

    def get_by_market(
        self,
        canonical_market_id: str,
    ) -> CertifiedMarketClassification | None:
        return self._by_market_id.get(
            _text(canonical_market_id, "canonical_market_id")
        )

    def get(
        self,
        classification_id: str,
    ) -> CertifiedMarketClassification | None:
        return self._by_classification_id.get(
            _text(classification_id, "classification_id")
        )

    def by_category(
        self,
        category_id: str,
    ) -> Tuple[CertifiedMarketClassification, ...]:
        return self._by_category_id.get(
            _text(category_id, "category_id").lower(),
            (),
        )

    def unclassified_market_ids(self) -> Tuple[str, ...]:
        return tuple(
            market.canonical_market_id
            for market in self.markets
            if market.canonical_market_id not in self._by_market_id
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "read_only",
            "classifications": self.classifications,
            "market_record_hashes": tuple(
                market.record_hash for market in self.markets
            ),
            "category_registry_hash": self.category_registry.registry_hash,
            "registry_lineage": self.registry_lineage,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class MarketClassificationCertificationResult:
    certified: bool
    registry_hash: str
    classification_count: int
    unclassified_market_ids: Tuple[str, ...]
    checks: Mapping[str, bool]
    failed_checks: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "checks",
            MappingProxyType(dict(self.checks)),
        )

@dataclass(frozen=True, slots=True)
class UMD006CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    registry_mode: str
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
            "registry_mode": self.registry_mode,
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

def build_umd_006_certification_manifest() -> UMD006CertificationManifest:
    return UMD006CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_006_BUILD_ID,
        build_name=UMD_006_BUILD_NAME,
        revision=UMD_006_REVISION,
        schema_version=UMD_006_SCHEMA_VERSION,
        upstream_builds=(
            "UMD-001",
            "UMD-002",
            "UMD-003",
            "UMD-004",
            "UMD-005",
        ),
        registry_mode="read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )

def certify_market_classification_registry(
    registry: ReadOnlyMarketClassificationRegistry,
    *,
    require_all_markets_classified: bool = True,
) -> MarketClassificationCertificationResult:
    unclassified = registry.unclassified_market_ids()
    checks = {
        "registry_hash_length": len(registry.registry_hash) == 64,
        "classification_ids_unique": len(
            {
                classification.classification_id
                for classification in registry.classifications
            }
        ) == len(registry.classifications),
        "market_classifications_unique": len(
            {
                classification.canonical_market_id
                for classification in registry.classifications
            }
        ) == len(registry.classifications),
        "all_markets_resolve": all(
            registry.get_by_market(classification.canonical_market_id)
            is not None
            for classification in registry.classifications
        ),
        "all_categories_resolve": all(
            registry.category_registry.get(classification.category_id)
            is not None
            for classification in registry.classifications
        ),
        "all_lineage_certified": all(
            classification.lineage.subsystem_id == "UMD"
            and classification.lineage.build_id == "UMD-006"
            for classification in registry.classifications
        ),
        "deterministic_ordering": tuple(
            classification.classification_id
            for classification in registry.classifications
        ) == tuple(
            sorted(
                classification.classification_id
                for classification in registry.classifications
            )
        ),
        "deterministic_replay": registry.registry_hash
        == deterministic_sha256(registry.to_canonical_dict()),
        "all_markets_classified": (
            not unclassified
            if require_all_markets_classified
            else True
        ),
        "registry_maps_read_only": isinstance(
            registry._by_market_id,
            MappingProxyType,
        )
        and isinstance(
            registry._by_classification_id,
            MappingProxyType,
        )
        and isinstance(
            registry._by_category_id,
            MappingProxyType,
        ),
    }
    failed = tuple(
        name for name, passed in checks.items() if not passed
    )
    return MarketClassificationCertificationResult(
        certified=not failed,
        registry_hash=registry.registry_hash,
        classification_count=len(registry.classifications),
        unclassified_market_ids=unclassified,
        checks=checks,
        failed_checks=failed,
    )

def certify_umd_006_foundation() -> Mapping[str, Any]:
    manifest = build_umd_006_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-006",
        "upstreams_frozen": manifest.upstream_builds
        == (
            "UMD-001",
            "UMD-002",
            "UMD-003",
            "UMD-004",
            "UMD-005",
        ),
        "read_only": manifest.registry_mode == "read_only",
        "network_disabled": manifest.network_enabled is False,
        "persistence_disabled": manifest.persistence_enabled is False,
        "mutation_disabled": manifest.mutation_enabled is False,
        "publication_disabled": manifest.publication_enabled is False,
        "execution_disabled": manifest.execution_enabled is False,
        "deterministic_manifest_hash": manifest.manifest_hash
        == deterministic_sha256(manifest.to_canonical_dict()),
    }
    failed = tuple(
        name for name, passed in checks.items() if not passed
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

def verify_umd_006_certified_market_classification_registry() -> bool:
    result = certify_umd_006_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-006 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True

__all__ = [
    "UMD_006_BUILD_ID",
    "UMD_006_BUILD_NAME",
    "UMD_006_REVISION",
    "UMD_006_SCHEMA_VERSION",
    "CertifiedMarketClassification",
    "ReadOnlyMarketClassificationRegistry",
    "MarketClassificationCertificationResult",
    "UMD006CertificationManifest",
    "build_umd_006_certification_manifest",
    "certify_market_classification_registry",
    "certify_umd_006_foundation",
    "verify_umd_006_certified_market_classification_registry",
]
