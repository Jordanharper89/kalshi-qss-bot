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

UMD_005_BUILD_ID = "UMD-005"
UMD_005_BUILD_NAME = "Certified Market Category Hierarchy Registry"
UMD_005_REVISION = "UMD_005_CERTIFIED_MARKET_CATEGORY_HIERARCHY_REGISTRY_V1"
UMD_005_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "venue_api_connection",
    "credential_loading",
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

def _slug(value: str, name: str) -> str:
    normalized = _text(value, name).lower()
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    if any(ch not in allowed for ch in normalized):
        raise ValueError(
            f"{name} may contain only lowercase letters, digits, hyphen, and underscore"
        )
    return normalized

def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(sorted((str(key), item) for key, item in value.items())))

def _unique(values: Tuple[str, ...], name: str) -> Tuple[str, ...]:
    return tuple(sorted({_slug(value, name) for value in values}))

@dataclass(frozen=True, slots=True)
class CertifiedMarketCategoryNode:
    category_id: str
    canonical_name: str
    parent_category_id: str | None
    aliases: Tuple[str, ...]
    description: str | None
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(self, "category_id", _slug(self.category_id, "category_id"))
        object.__setattr__(
            self,
            "canonical_name",
            _text(self.canonical_name, "canonical_name"),
        )
        if self.parent_category_id is not None:
            parent = _slug(self.parent_category_id, "parent_category_id")
            if parent == self.category_id:
                raise ValueError("category cannot be its own parent")
            object.__setattr__(self, "parent_category_id", parent)

        aliases = tuple(sorted({_text(alias, "alias") for alias in self.aliases}))
        if self.canonical_name.casefold() in {alias.casefold() for alias in aliases}:
            raise ValueError("aliases must not repeat canonical_name")
        object.__setattr__(self, "aliases", aliases)

        if self.description is not None:
            object.__setattr__(
                self,
                "description",
                _text(self.description, "description"),
            )
        object.__setattr__(self, "metadata", _freeze(self.metadata))

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("category lineage must belong to UMD")
        if self.lineage.build_id != UMD_005_BUILD_ID:
            raise ValueError("category lineage must use build_id UMD-005")

    def identity_payload(self) -> Mapping[str, Any]:
        return {"category_id": self.category_id}

    @property
    def canonical_category_id(self) -> str:
        return f"umd:category:{deterministic_sha256(self.identity_payload())}"

    @property
    def alias_keys(self) -> Tuple[str, ...]:
        values = (self.category_id, self.canonical_name, *self.aliases)
        return tuple(sorted({_text(value, "alias_key").casefold() for value in values}))

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "canonical_category_id": self.canonical_category_id,
            "category_id": self.category_id,
            "canonical_name": self.canonical_name,
            "parent_category_id": self.parent_category_id,
            "aliases": self.aliases,
            "description": self.description,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class ReadOnlyMarketCategoryHierarchyRegistry:
    categories: Tuple[CertifiedMarketCategoryNode, ...]
    registry_lineage: ImmutableLineage
    _by_category_id: Mapping[str, CertifiedMarketCategoryNode] = field(
        init=False, repr=False
    )
    _alias_index: Mapping[str, str] = field(init=False, repr=False)
    _children: Mapping[str, Tuple[str, ...]] = field(init=False, repr=False)
    _paths: Mapping[str, Tuple[str, ...]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.categories, key=lambda item: item.category_id))
        object.__setattr__(self, "categories", ordered)

        if self.registry_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("registry lineage must belong to UMD")
        if self.registry_lineage.build_id != UMD_005_BUILD_ID:
            raise ValueError("registry lineage must use build_id UMD-005")

        by_id = {}
        alias_index = {}
        children = {}

        for category in ordered:
            if category.category_id in by_id:
                raise ValueError(f"duplicate category_id: {category.category_id}")
            by_id[category.category_id] = category

        for category in ordered:
            parent = category.parent_category_id
            if parent is not None and parent not in by_id:
                raise ValueError(
                    f"unknown parent category '{parent}' for '{category.category_id}'"
                )
            if parent is not None:
                children.setdefault(parent, []).append(category.category_id)

            for alias_key in category.alias_keys:
                existing = alias_index.get(alias_key)
                if existing is not None and existing != category.category_id:
                    raise ValueError(f"ambiguous category alias '{alias_key}'")
                alias_index[alias_key] = category.category_id

        paths = {}
        visiting = set()

        def resolve_path(category_id: str) -> Tuple[str, ...]:
            if category_id in paths:
                return paths[category_id]
            if category_id in visiting:
                raise ValueError(f"category hierarchy cycle detected at '{category_id}'")
            visiting.add(category_id)
            node = by_id[category_id]
            if node.parent_category_id is None:
                path = (category_id,)
            else:
                path = resolve_path(node.parent_category_id) + (category_id,)
            visiting.remove(category_id)
            paths[category_id] = path
            return path

        for category_id in by_id:
            resolve_path(category_id)

        frozen_children = {
            parent: tuple(sorted(values))
            for parent, values in children.items()
        }

        object.__setattr__(self, "_by_category_id", MappingProxyType(by_id))
        object.__setattr__(self, "_alias_index", MappingProxyType(alias_index))
        object.__setattr__(self, "_children", MappingProxyType(frozen_children))
        object.__setattr__(self, "_paths", MappingProxyType(paths))

    def get(self, category_id: str) -> CertifiedMarketCategoryNode | None:
        return self._by_category_id.get(_slug(category_id, "category_id"))

    def resolve_alias(self, alias: str) -> CertifiedMarketCategoryNode | None:
        category_id = self._alias_index.get(_text(alias, "alias").casefold())
        if category_id is None:
            return None
        return self._by_category_id[category_id]

    def path_for(self, category_id: str) -> Tuple[str, ...]:
        normalized = _slug(category_id, "category_id")
        if normalized not in self._paths:
            raise KeyError(normalized)
        return self._paths[normalized]

    def children_of(self, category_id: str) -> Tuple[CertifiedMarketCategoryNode, ...]:
        normalized = _slug(category_id, "category_id")
        return tuple(
            self._by_category_id[child_id]
            for child_id in self._children.get(normalized, ())
        )

    def roots(self) -> Tuple[CertifiedMarketCategoryNode, ...]:
        return tuple(
            category
            for category in self.categories
            if category.parent_category_id is None
        )

    def validate_market(
        self,
        market: CertifiedCanonicalMarket,
    ) -> bool:
        category = self.get(market.category.category_id)
        if category is None:
            raise ValueError(
                f"market category is not registered: {market.category.category_id}"
            )
        expected_path = self.path_for(category.category_id)
        if market.category.path and tuple(market.category.path) != expected_path:
            raise ValueError(
                "market category path does not match certified hierarchy"
            )
        if market.category.parent_category_id != category.parent_category_id:
            raise ValueError(
                "market category parent does not match certified hierarchy"
            )
        return True

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "read_only",
            "categories": self.categories,
            "resolved_paths": tuple(
                (category_id, self._paths[category_id])
                for category_id in sorted(self._paths)
            ),
            "registry_lineage": self.registry_lineage,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class MarketCategoryHierarchyCertificationResult:
    certified: bool
    registry_hash: str
    category_count: int
    root_count: int
    checks: Mapping[str, bool]
    failed_checks: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "checks", MappingProxyType(dict(self.checks)))

@dataclass(frozen=True, slots=True)
class UMD005CertificationManifest:
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

def build_umd_005_certification_manifest() -> UMD005CertificationManifest:
    return UMD005CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_005_BUILD_ID,
        build_name=UMD_005_BUILD_NAME,
        revision=UMD_005_REVISION,
        schema_version=UMD_005_SCHEMA_VERSION,
        upstream_builds=("UMD-001", "UMD-002", "UMD-003", "UMD-004"),
        registry_mode="read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )

def certify_market_category_hierarchy_registry(
    registry: ReadOnlyMarketCategoryHierarchyRegistry,
) -> MarketCategoryHierarchyCertificationResult:
    checks = {
        "registry_hash_length": len(registry.registry_hash) == 64,
        "category_ids_unique": len(
            {category.category_id for category in registry.categories}
        ) == len(registry.categories),
        "canonical_ids_unique": len(
            {category.canonical_category_id for category in registry.categories}
        ) == len(registry.categories),
        "all_parents_resolve": all(
            category.parent_category_id is None
            or registry.get(category.parent_category_id) is not None
            for category in registry.categories
        ),
        "all_paths_resolve": all(
            registry.path_for(category.category_id)[-1] == category.category_id
            for category in registry.categories
        ),
        "all_lineage_certified": all(
            category.lineage.subsystem_id == "UMD"
            and category.lineage.build_id == "UMD-005"
            for category in registry.categories
        ),
        "deterministic_ordering": tuple(
            category.category_id for category in registry.categories
        ) == tuple(sorted(category.category_id for category in registry.categories)),
        "deterministic_replay": registry.registry_hash
        == deterministic_sha256(registry.to_canonical_dict()),
        "registry_maps_read_only": isinstance(
            registry._by_category_id, MappingProxyType
        )
        and isinstance(registry._alias_index, MappingProxyType)
        and isinstance(registry._children, MappingProxyType)
        and isinstance(registry._paths, MappingProxyType),
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    return MarketCategoryHierarchyCertificationResult(
        certified=not failed,
        registry_hash=registry.registry_hash,
        category_count=len(registry.categories),
        root_count=len(registry.roots()),
        checks=checks,
        failed_checks=failed,
    )

def certify_umd_005_foundation() -> Mapping[str, Any]:
    manifest = build_umd_005_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-005",
        "upstreams_frozen": manifest.upstream_builds
        == ("UMD-001", "UMD-002", "UMD-003", "UMD-004"),
        "read_only": manifest.registry_mode == "read_only",
        "network_disabled": manifest.network_enabled is False,
        "persistence_disabled": manifest.persistence_enabled is False,
        "mutation_disabled": manifest.mutation_enabled is False,
        "publication_disabled": manifest.publication_enabled is False,
        "execution_disabled": manifest.execution_enabled is False,
        "deterministic_manifest_hash": manifest.manifest_hash
        == deterministic_sha256(manifest.to_canonical_dict()),
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
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

def verify_umd_005_certified_market_category_hierarchy_registry() -> bool:
    result = certify_umd_005_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-005 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True

__all__ = [
    "UMD_005_BUILD_ID",
    "UMD_005_BUILD_NAME",
    "UMD_005_REVISION",
    "UMD_005_SCHEMA_VERSION",
    "CertifiedMarketCategoryNode",
    "ReadOnlyMarketCategoryHierarchyRegistry",
    "MarketCategoryHierarchyCertificationResult",
    "UMD005CertificationManifest",
    "build_umd_005_certification_manifest",
    "certify_market_category_hierarchy_registry",
    "certify_umd_005_foundation",
    "verify_umd_005_certified_market_category_hierarchy_registry",
]
