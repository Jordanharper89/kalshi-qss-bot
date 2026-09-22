from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_canonical_market_contract import CertifiedCanonicalMarket
from .certified_active_canonical_market_registry_read_model import (
    CertifiedActiveCanonicalMarketRegistryReadModel,
)

UMD_023_BUILD_ID = "UMD-023"
UMD_023_BUILD_NAME = "Certified Active Canonical Market Registry Query Contract"
UMD_023_REVISION = (
    "UMD_023_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_QUERY_CONTRACT_V1"
)
UMD_023_SCHEMA_VERSION = "1.0.0"

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


def _optional_text(
    value: str | None,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    return _text(value, field_name).lower()


def _value_text(value: Any) -> str:
    raw = getattr(value, "value", value)
    return str(raw).strip().lower()


class MarketQueryMode(str, Enum):
    BY_ID = "by_id"
    FILTER = "filter"
    ALL = "all"


@dataclass(frozen=True, slots=True)
class CertifiedActiveMarketQueryRequest:
    query_mode: MarketQueryMode
    canonical_market_id: str | None
    venue_id: str | None
    category_id: str | None
    lifecycle: str | None
    limit: int | None
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        if not isinstance(self.query_mode, MarketQueryMode):
            object.__setattr__(
                self,
                "query_mode",
                MarketQueryMode(self.query_mode),
            )

        market_id = (
            None
            if self.canonical_market_id is None
            else _text(
                self.canonical_market_id,
                "canonical_market_id",
            )
        )
        if market_id is not None and not market_id.startswith(
            "umd:mkt:"
        ):
            raise ValueError(
                "canonical_market_id must use UMD market prefix"
            )
        object.__setattr__(
            self,
            "canonical_market_id",
            market_id,
        )

        object.__setattr__(
            self,
            "venue_id",
            _optional_text(
                self.venue_id,
                "venue_id",
            ),
        )
        object.__setattr__(
            self,
            "category_id",
            _optional_text(
                self.category_id,
                "category_id",
            ),
        )
        object.__setattr__(
            self,
            "lifecycle",
            (
                None
                if self.lifecycle is None
                else _value_text(self.lifecycle)
            ),
        )

        if self.limit is not None:
            if not isinstance(self.limit, int):
                raise TypeError("limit must be an integer or None")
            if self.limit < 1:
                raise ValueError("limit must be positive")

        if self.query_mode == MarketQueryMode.BY_ID:
            if self.canonical_market_id is None:
                raise ValueError(
                    "BY_ID query requires canonical_market_id"
                )
            if any(
                value is not None
                for value in (
                    self.venue_id,
                    self.category_id,
                    self.lifecycle,
                    self.limit,
                )
            ):
                raise ValueError(
                    "BY_ID query cannot include filters or limit"
                )

        if self.query_mode == MarketQueryMode.ALL:
            if any(
                value is not None
                for value in (
                    self.canonical_market_id,
                    self.venue_id,
                    self.category_id,
                    self.lifecycle,
                )
            ):
                raise ValueError(
                    "ALL query cannot include identity or filters"
                )

        if self.query_mode == MarketQueryMode.FILTER:
            if self.canonical_market_id is not None:
                raise ValueError(
                    "FILTER query cannot include canonical_market_id"
                )
            if all(
                value is None
                for value in (
                    self.venue_id,
                    self.category_id,
                    self.lifecycle,
                )
            ):
                raise ValueError(
                    "FILTER query requires at least one filter"
                )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("query lineage must belong to UMD")
        if self.lineage.build_id != UMD_023_BUILD_ID:
            raise ValueError(
                "query lineage must use build_id UMD-023"
            )

    @property
    def query_id(self) -> str:
        return "umd:market-query:" + deterministic_sha256(
            self.to_canonical_dict()
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "query_mode": self.query_mode,
            "canonical_market_id": self.canonical_market_id,
            "venue_id": self.venue_id,
            "category_id": self.category_id,
            "lifecycle": self.lifecycle,
            "limit": self.limit,
            "lineage": self.lineage,
        }


@dataclass(frozen=True, slots=True)
class CertifiedActiveMarketQueryResult:
    query: CertifiedActiveMarketQueryRequest
    active_snapshot_id: str
    active_snapshot_hash: str
    read_model_hash: str
    markets: Tuple[CertifiedCanonicalMarket, ...]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        snapshot_id = _text(
            self.active_snapshot_id,
            "active_snapshot_id",
        )
        if not snapshot_id.startswith(
            "umd:market-registry-snapshot:"
        ):
            raise ValueError(
                "active_snapshot_id must use UMD snapshot prefix"
            )
        object.__setattr__(
            self,
            "active_snapshot_id",
            snapshot_id,
        )

        for field_name in (
            "active_snapshot_hash",
            "read_model_hash",
        ):
            value = _text(
                getattr(self, field_name),
                field_name,
            ).lower()
            if len(value) != 64:
                raise ValueError(
                    f"{field_name} must contain 64 hexadecimal characters"
                )
            if any(
                character not in "0123456789abcdef"
                for character in value
            ):
                raise ValueError(
                    f"{field_name} must be lowercase SHA-256 hexadecimal"
                )
            object.__setattr__(
                self,
                field_name,
                value,
            )

        markets = tuple(
            sorted(
                self.markets,
                key=lambda market: market.canonical_market_id,
            )
        )
        if len(
            {
                market.canonical_market_id
                for market in markets
            }
        ) != len(markets):
            raise ValueError(
                "query result contains duplicate canonical market IDs"
            )
        object.__setattr__(
            self,
            "markets",
            markets,
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError(
                "query-result lineage must belong to UMD"
            )
        if self.lineage.build_id != UMD_023_BUILD_ID:
            raise ValueError(
                "query-result lineage must use build_id UMD-023"
            )

        required_parents = {
            self.read_model_hash,
        }
        if not required_parents.issubset(
            set(self.lineage.parent_hashes)
        ):
            raise ValueError(
                "query-result lineage must include read-model hash"
            )

    @property
    def result_id(self) -> str:
        return "umd:market-query-result:" + deterministic_sha256(
            {
                "query_id": self.query.query_id,
                "active_snapshot_id": self.active_snapshot_id,
                "active_snapshot_hash": self.active_snapshot_hash,
                "read_model_hash": self.read_model_hash,
                "market_record_hashes": tuple(
                    market.record_hash
                    for market in self.markets
                ),
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "result_id": self.result_id,
            "query": self.query,
            "active_snapshot_id": self.active_snapshot_id,
            "active_snapshot_hash": self.active_snapshot_hash,
            "read_model_hash": self.read_model_hash,
            "markets": self.markets,
            "lineage": self.lineage,
        }

    @property
    def result_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def execute_active_market_query(
    request: CertifiedActiveMarketQueryRequest,
    read_model: CertifiedActiveCanonicalMarketRegistryReadModel,
    *,
    lineage: ImmutableLineage,
) -> CertifiedActiveMarketQueryResult:
    if request.query_mode == MarketQueryMode.BY_ID:
        market = read_model.get(
            request.canonical_market_id
        )
        markets = () if market is None else (market,)

    elif request.query_mode == MarketQueryMode.ALL:
        markets = tuple(
            read_model.get(market_id)
            for market_id in read_model.market_ids()
        )

    else:
        candidate_ids = set(read_model.market_ids())

        if request.venue_id is not None:
            candidate_ids &= {
                market.canonical_market_id
                for market in read_model.by_venue(
                    request.venue_id
                )
            }

        if request.category_id is not None:
            candidate_ids &= {
                market.canonical_market_id
                for market in read_model.by_category(
                    request.category_id
                )
            }

        if request.lifecycle is not None:
            candidate_ids &= {
                market.canonical_market_id
                for market in read_model.by_lifecycle(
                    request.lifecycle
                )
            }

        markets = tuple(
            read_model.get(market_id)
            for market_id in sorted(candidate_ids)
        )

    markets = tuple(
        market
        for market in markets
        if market is not None
    )

    if request.limit is not None:
        markets = markets[: request.limit]

    return CertifiedActiveMarketQueryResult(
        query=request,
        active_snapshot_id=read_model.active_snapshot_id,
        active_snapshot_hash=read_model.active_snapshot_hash,
        read_model_hash=read_model.read_model_hash,
        markets=markets,
        lineage=lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD023CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    query_mode: str
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
            "query_mode": self.query_mode,
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


def build_umd_023_certification_manifest() -> UMD023CertificationManifest:
    return UMD023CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_023_BUILD_ID,
        build_name=UMD_023_BUILD_NAME,
        revision=UMD_023_REVISION,
        schema_version=UMD_023_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 23)
        ),
        query_mode="deterministic_read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_023_foundation() -> Mapping[str, Any]:
    manifest = build_umd_023_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-023"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 23)
            )
        ),
        "deterministic_read_only": (
            manifest.query_mode
            == "deterministic_read_only"
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


def verify_umd_023_certified_active_canonical_market_registry_query_contract() -> bool:
    result = certify_umd_023_foundation()

    if not result["certified"]:
        raise RuntimeError(
            "UMD-023 certification failed: "
            + ", ".join(result["failed_checks"])
        )

    return True


__all__ = [
    "UMD_023_BUILD_ID",
    "UMD_023_BUILD_NAME",
    "UMD_023_REVISION",
    "UMD_023_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "MarketQueryMode",
    "CertifiedActiveMarketQueryRequest",
    "CertifiedActiveMarketQueryResult",
    "execute_active_market_query",
    "UMD023CertificationManifest",
    "build_umd_023_certification_manifest",
    "certify_umd_023_foundation",
    "verify_umd_023_certified_active_canonical_market_registry_query_contract",
]
