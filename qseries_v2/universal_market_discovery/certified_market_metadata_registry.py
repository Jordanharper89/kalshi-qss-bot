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
from .certified_market_classification_registry import (
    ReadOnlyMarketClassificationRegistry,
)

UMD_007_BUILD_ID = "UMD-007"
UMD_007_BUILD_NAME = "Certified Market Metadata Registry"
UMD_007_REVISION = "UMD_007_CERTIFIED_MARKET_METADATA_REGISTRY_V1"
UMD_007_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "venue_api_connection",
    "credential_loading",
    "automatic_metadata_enrichment",
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

def _optional_text(value: str | None, name: str) -> str | None:
    return None if value is None else _text(value, name)

def _slug(value: str, name: str) -> str:
    normalized = _text(value, name).lower()
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    if any(ch not in allowed for ch in normalized):
        raise ValueError(
            f"{name} may contain only lowercase letters, digits, hyphen, and underscore"
        )
    return normalized

def _symbol(value: str, name: str) -> str:
    normalized = _text(value, name).upper()
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-"
    if any(ch not in allowed for ch in normalized):
        raise ValueError(f"{name} contains unsupported characters")
    return normalized

def _unique_text(values: Tuple[str, ...], name: str) -> Tuple[str, ...]:
    return tuple(sorted({_text(value, name) for value in values}))

def _unique_slug(values: Tuple[str, ...], name: str) -> Tuple[str, ...]:
    return tuple(sorted({_slug(value, name) for value in values}))

def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(
        dict(sorted((str(key), item) for key, item in value.items()))
    )

@dataclass(frozen=True, slots=True)
class CertifiedMarketMetadata:
    canonical_market_id: str
    display_title: str
    short_title: str | None
    description: str | None
    symbol: str | None
    language: str
    timezone_name: str
    quote_currency: str
    tags: Tuple[str, ...]
    keywords: Tuple[str, ...]
    external_reference_ids: Mapping[str, str]
    metadata_version: str
    attributes: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        market_id = _text(self.canonical_market_id, "canonical_market_id")
        if not market_id.startswith("umd:mkt:"):
            raise ValueError("canonical_market_id must use the UMD market prefix")
        object.__setattr__(self, "canonical_market_id", market_id)

        object.__setattr__(
            self,
            "display_title",
            _text(self.display_title, "display_title"),
        )
        object.__setattr__(
            self,
            "short_title",
            _optional_text(self.short_title, "short_title"),
        )
        object.__setattr__(
            self,
            "description",
            _optional_text(self.description, "description"),
        )
        if self.symbol is not None:
            object.__setattr__(
                self,
                "symbol",
                _symbol(self.symbol, "symbol"),
            )

        object.__setattr__(
            self,
            "language",
            _slug(self.language, "language"),
        )
        object.__setattr__(
            self,
            "timezone_name",
            _text(self.timezone_name, "timezone_name"),
        )
        object.__setattr__(
            self,
            "quote_currency",
            _symbol(self.quote_currency, "quote_currency"),
        )
        object.__setattr__(
            self,
            "tags",
            _unique_slug(self.tags, "tag"),
        )
        object.__setattr__(
            self,
            "keywords",
            _unique_text(self.keywords, "keyword"),
        )

        references = {}
        for namespace, reference_id in self.external_reference_ids.items():
            normalized_namespace = _slug(str(namespace), "reference namespace")
            normalized_reference = _text(str(reference_id), "reference id")
            if normalized_namespace in references:
                raise ValueError(
                    f"duplicate external reference namespace: {normalized_namespace}"
                )
            references[normalized_namespace] = normalized_reference
        object.__setattr__(
            self,
            "external_reference_ids",
            MappingProxyType(dict(sorted(references.items()))),
        )

        object.__setattr__(
            self,
            "metadata_version",
            _text(self.metadata_version, "metadata_version"),
        )
        object.__setattr__(
            self,
            "attributes",
            _freeze(self.attributes),
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("metadata lineage must belong to UMD")
        if self.lineage.build_id != UMD_007_BUILD_ID:
            raise ValueError("metadata lineage must use build_id UMD-007")

    @classmethod
    def from_market(
        cls,
        market: CertifiedCanonicalMarket,
        *,
        short_title: str | None,
        symbol: str | None,
        language: str,
        timezone_name: str,
        tags: Tuple[str, ...],
        keywords: Tuple[str, ...],
        external_reference_ids: Mapping[str, str],
        metadata_version: str,
        attributes: Mapping[str, Any],
        lineage: ImmutableLineage,
    ) -> "CertifiedMarketMetadata":
        return cls(
            canonical_market_id=market.canonical_market_id,
            display_title=market.canonical_title,
            short_title=short_title,
            description=market.canonical_description,
            symbol=symbol,
            language=language,
            timezone_name=timezone_name,
            quote_currency=market.quote_currency,
            tags=tags,
            keywords=keywords,
            external_reference_ids=external_reference_ids,
            metadata_version=metadata_version,
            attributes=attributes,
            lineage=lineage,
        )

    def identity_payload(self) -> Mapping[str, Any]:
        return {"canonical_market_id": self.canonical_market_id}

    @property
    def metadata_id(self) -> str:
        return f"umd:metadata:{deterministic_sha256(self.identity_payload())}"

    def content_payload(self) -> Mapping[str, Any]:
        return {
            "display_title": self.display_title,
            "short_title": self.short_title,
            "description": self.description,
            "symbol": self.symbol,
            "language": self.language,
            "timezone_name": self.timezone_name,
            "quote_currency": self.quote_currency,
            "tags": self.tags,
            "keywords": self.keywords,
            "external_reference_ids": self.external_reference_ids,
            "metadata_version": self.metadata_version,
            "attributes": self.attributes,
        }

    @property
    def content_fingerprint(self) -> str:
        return deterministic_sha256(self.content_payload())

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "metadata_id": self.metadata_id,
            "canonical_market_id": self.canonical_market_id,
            **self.content_payload(),
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class ReadOnlyMarketMetadataRegistry:
    metadata_records: Tuple[CertifiedMarketMetadata, ...]
    markets: Tuple[CertifiedCanonicalMarket, ...]
    classification_registry: ReadOnlyMarketClassificationRegistry
    registry_lineage: ImmutableLineage
    _by_market_id: Mapping[str, CertifiedMarketMetadata] = field(
        init=False,
        repr=False,
    )
    _by_metadata_id: Mapping[str, CertifiedMarketMetadata] = field(
        init=False,
        repr=False,
    )
    _by_tag: Mapping[str, Tuple[CertifiedMarketMetadata, ...]] = field(
        init=False,
        repr=False,
    )
    _reference_index: Mapping[Tuple[str, str], str] = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        ordered_records = tuple(
            sorted(
                self.metadata_records,
                key=lambda item: item.metadata_id,
            )
        )
        ordered_markets = tuple(
            sorted(
                self.markets,
                key=lambda item: item.canonical_market_id,
            )
        )
        object.__setattr__(self, "metadata_records", ordered_records)
        object.__setattr__(self, "markets", ordered_markets)

        if self.registry_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("registry lineage must belong to UMD")
        if self.registry_lineage.build_id != UMD_007_BUILD_ID:
            raise ValueError("registry lineage must use build_id UMD-007")

        market_by_id = {
            market.canonical_market_id: market
            for market in ordered_markets
        }
        if len(market_by_id) != len(ordered_markets):
            raise ValueError("duplicate canonical market IDs supplied")

        by_market_id = {}
        by_metadata_id = {}
        tag_groups = {}
        reference_index = {}

        for record in ordered_records:
            if record.metadata_id in by_metadata_id:
                raise ValueError("duplicate metadata ID")
            if record.canonical_market_id in by_market_id:
                raise ValueError(
                    "canonical market may have only one certified metadata record"
                )

            market = market_by_id.get(record.canonical_market_id)
            if market is None:
                raise ValueError(
                    f"unknown canonical market ID: {record.canonical_market_id}"
                )

            classification = self.classification_registry.get_by_market(
                record.canonical_market_id
            )
            if classification is None:
                raise ValueError(
                    "market metadata requires a certified classification"
                )

            if record.display_title != market.canonical_title:
                raise ValueError("display_title must match canonical market title")
            if record.description != market.canonical_description:
                raise ValueError(
                    "description must match canonical market description"
                )
            if record.quote_currency != market.quote_currency:
                raise ValueError(
                    "quote_currency must match canonical market currency"
                )

            for namespace, reference_id in record.external_reference_ids.items():
                key = (namespace, reference_id)
                existing = reference_index.get(key)
                if existing is not None and existing != record.canonical_market_id:
                    raise ValueError(
                        "duplicate external reference identity across markets"
                    )
                reference_index[key] = record.canonical_market_id

            by_market_id[record.canonical_market_id] = record
            by_metadata_id[record.metadata_id] = record

            for tag in record.tags:
                tag_groups.setdefault(tag, []).append(record)

        frozen_tag_groups = {
            tag: tuple(
                sorted(
                    records,
                    key=lambda item: item.canonical_market_id,
                )
            )
            for tag, records in tag_groups.items()
        }

        object.__setattr__(
            self,
            "_by_market_id",
            MappingProxyType(by_market_id),
        )
        object.__setattr__(
            self,
            "_by_metadata_id",
            MappingProxyType(by_metadata_id),
        )
        object.__setattr__(
            self,
            "_by_tag",
            MappingProxyType(frozen_tag_groups),
        )
        object.__setattr__(
            self,
            "_reference_index",
            MappingProxyType(reference_index),
        )

    def get_by_market(
        self,
        canonical_market_id: str,
    ) -> CertifiedMarketMetadata | None:
        return self._by_market_id.get(
            _text(canonical_market_id, "canonical_market_id")
        )

    def get(
        self,
        metadata_id: str,
    ) -> CertifiedMarketMetadata | None:
        return self._by_metadata_id.get(
            _text(metadata_id, "metadata_id")
        )

    def by_tag(
        self,
        tag: str,
    ) -> Tuple[CertifiedMarketMetadata, ...]:
        return self._by_tag.get(_slug(tag, "tag"), ())

    def resolve_external_reference(
        self,
        namespace: str,
        reference_id: str,
    ) -> CertifiedMarketMetadata | None:
        market_id = self._reference_index.get(
            (
                _slug(namespace, "reference namespace"),
                _text(reference_id, "reference id"),
            )
        )
        if market_id is None:
            return None
        return self._by_market_id[market_id]

    def missing_metadata_market_ids(self) -> Tuple[str, ...]:
        return tuple(
            market.canonical_market_id
            for market in self.markets
            if market.canonical_market_id not in self._by_market_id
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "read_only",
            "metadata_records": self.metadata_records,
            "market_record_hashes": tuple(
                market.record_hash for market in self.markets
            ),
            "classification_registry_hash": (
                self.classification_registry.registry_hash
            ),
            "registry_lineage": self.registry_lineage,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class MarketMetadataCertificationResult:
    certified: bool
    registry_hash: str
    metadata_count: int
    missing_metadata_market_ids: Tuple[str, ...]
    checks: Mapping[str, bool]
    failed_checks: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "checks",
            MappingProxyType(dict(self.checks)),
        )

@dataclass(frozen=True, slots=True)
class UMD007CertificationManifest:
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

def build_umd_007_certification_manifest() -> UMD007CertificationManifest:
    return UMD007CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_007_BUILD_ID,
        build_name=UMD_007_BUILD_NAME,
        revision=UMD_007_REVISION,
        schema_version=UMD_007_SCHEMA_VERSION,
        upstream_builds=(
            "UMD-001",
            "UMD-002",
            "UMD-003",
            "UMD-004",
            "UMD-005",
            "UMD-006",
        ),
        registry_mode="read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )

def certify_market_metadata_registry(
    registry: ReadOnlyMarketMetadataRegistry,
    *,
    require_all_markets_described: bool = True,
) -> MarketMetadataCertificationResult:
    missing = registry.missing_metadata_market_ids()
    checks = {
        "registry_hash_length": len(registry.registry_hash) == 64,
        "metadata_ids_unique": len(
            {record.metadata_id for record in registry.metadata_records}
        ) == len(registry.metadata_records),
        "market_metadata_unique": len(
            {
                record.canonical_market_id
                for record in registry.metadata_records
            }
        ) == len(registry.metadata_records),
        "all_markets_resolve": all(
            registry.get_by_market(record.canonical_market_id) is not None
            for record in registry.metadata_records
        ),
        "all_classifications_resolve": all(
            registry.classification_registry.get_by_market(
                record.canonical_market_id
            )
            is not None
            for record in registry.metadata_records
        ),
        "all_lineage_certified": all(
            record.lineage.subsystem_id == "UMD"
            and record.lineage.build_id == "UMD-007"
            for record in registry.metadata_records
        ),
        "deterministic_ordering": tuple(
            record.metadata_id for record in registry.metadata_records
        ) == tuple(
            sorted(
                record.metadata_id
                for record in registry.metadata_records
            )
        ),
        "deterministic_replay": registry.registry_hash
        == deterministic_sha256(registry.to_canonical_dict()),
        "all_markets_described": (
            not missing if require_all_markets_described else True
        ),
        "registry_maps_read_only": isinstance(
            registry._by_market_id,
            MappingProxyType,
        )
        and isinstance(
            registry._by_metadata_id,
            MappingProxyType,
        )
        and isinstance(
            registry._by_tag,
            MappingProxyType,
        )
        and isinstance(
            registry._reference_index,
            MappingProxyType,
        ),
    }
    failed = tuple(
        name for name, passed in checks.items() if not passed
    )
    return MarketMetadataCertificationResult(
        certified=not failed,
        registry_hash=registry.registry_hash,
        metadata_count=len(registry.metadata_records),
        missing_metadata_market_ids=missing,
        checks=checks,
        failed_checks=failed,
    )

def certify_umd_007_foundation() -> Mapping[str, Any]:
    manifest = build_umd_007_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-007",
        "upstreams_frozen": manifest.upstream_builds
        == (
            "UMD-001",
            "UMD-002",
            "UMD-003",
            "UMD-004",
            "UMD-005",
            "UMD-006",
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

def verify_umd_007_certified_market_metadata_registry() -> bool:
    result = certify_umd_007_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-007 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True

__all__ = [
    "UMD_007_BUILD_ID",
    "UMD_007_BUILD_NAME",
    "UMD_007_REVISION",
    "UMD_007_SCHEMA_VERSION",
    "CertifiedMarketMetadata",
    "ReadOnlyMarketMetadataRegistry",
    "MarketMetadataCertificationResult",
    "UMD007CertificationManifest",
    "build_umd_007_certification_manifest",
    "certify_market_metadata_registry",
    "certify_umd_007_foundation",
    "verify_umd_007_certified_market_metadata_registry",
]
