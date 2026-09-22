from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    MarketLifecycle,
    SettlementMethod,
    deterministic_sha256,
)
from .certified_canonical_market_contract import CertifiedCanonicalMarket
from .certified_market_metadata_registry import ReadOnlyMarketMetadataRegistry

UMD_008_BUILD_ID = "UMD-008"
UMD_008_BUILD_NAME = "Certified Market Lifecycle and Settlement Registry"
UMD_008_REVISION = "UMD_008_CERTIFIED_MARKET_LIFECYCLE_AND_SETTLEMENT_REGISTRY_V1"
UMD_008_SCHEMA_VERSION = "1.0.0"

ALLOWED_TRANSITIONS = MappingProxyType({
    MarketLifecycle.UNKNOWN: (
        MarketLifecycle.ANNOUNCED,
        MarketLifecycle.OPEN,
        MarketLifecycle.CANCELLED,
    ),
    MarketLifecycle.ANNOUNCED: (
        MarketLifecycle.OPEN,
        MarketLifecycle.CANCELLED,
    ),
    MarketLifecycle.OPEN: (
        MarketLifecycle.PAUSED,
        MarketLifecycle.CLOSED,
        MarketLifecycle.CANCELLED,
    ),
    MarketLifecycle.PAUSED: (
        MarketLifecycle.OPEN,
        MarketLifecycle.CLOSED,
        MarketLifecycle.CANCELLED,
    ),
    MarketLifecycle.CLOSED: (
        MarketLifecycle.EXPIRED,
        MarketLifecycle.SETTLING,
        MarketLifecycle.CANCELLED,
    ),
    MarketLifecycle.EXPIRED: (
        MarketLifecycle.SETTLING,
        MarketLifecycle.SETTLED,
        MarketLifecycle.CANCELLED,
    ),
    MarketLifecycle.SETTLING: (
        MarketLifecycle.SETTLED,
        MarketLifecycle.CANCELLED,
    ),
    MarketLifecycle.SETTLED: (),
    MarketLifecycle.CANCELLED: (),
})

def _text(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    value = " ".join(value.strip().split())
    if not value:
        raise ValueError(f"{name} must not be empty")
    return value

def _optional_text(value: str | None, name: str) -> str | None:
    return None if value is None else _text(value, name)

def _utc(value: datetime | None, name: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be datetime or None")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc)

def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(sorted((str(k), v) for k, v in value.items())))

@dataclass(frozen=True, slots=True)
class CertifiedMarketLifecycleSettlementRecord:
    canonical_market_id: str
    lifecycle: MarketLifecycle
    opens_at: datetime | None
    closes_at: datetime | None
    expires_at: datetime | None
    settles_at: datetime | None
    settlement_method: SettlementMethod
    settlement_source: str | None
    settlement_rule: str | None
    final_value: str | None
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        market_id = _text(self.canonical_market_id, "canonical_market_id")
        if not market_id.startswith("umd:mkt:"):
            raise ValueError("canonical_market_id must use UMD market prefix")
        object.__setattr__(self, "canonical_market_id", market_id)

        if not isinstance(self.lifecycle, MarketLifecycle):
            object.__setattr__(self, "lifecycle", MarketLifecycle(self.lifecycle))
        if not isinstance(self.settlement_method, SettlementMethod):
            object.__setattr__(
                self,
                "settlement_method",
                SettlementMethod(self.settlement_method),
            )

        values = {
            "opens_at": _utc(self.opens_at, "opens_at"),
            "closes_at": _utc(self.closes_at, "closes_at"),
            "expires_at": _utc(self.expires_at, "expires_at"),
            "settles_at": _utc(self.settles_at, "settles_at"),
        }
        for name, value in values.items():
            object.__setattr__(self, name, value)

        ordered = [v for v in values.values() if v is not None]
        if ordered != sorted(ordered):
            raise ValueError(
                "timestamps must satisfy opens_at <= closes_at <= expires_at <= settles_at"
            )

        object.__setattr__(
            self,
            "settlement_source",
            _optional_text(self.settlement_source, "settlement_source"),
        )
        object.__setattr__(
            self,
            "settlement_rule",
            _optional_text(self.settlement_rule, "settlement_rule"),
        )
        object.__setattr__(
            self,
            "final_value",
            _optional_text(self.final_value, "final_value"),
        )
        object.__setattr__(self, "metadata", _freeze(self.metadata))

        if self.lifecycle == MarketLifecycle.SETTLED:
            if self.final_value is None or self.settles_at is None:
                raise ValueError(
                    "settled markets require final_value and settles_at"
                )
        elif self.final_value is not None:
            raise ValueError("final_value is allowed only for settled markets")

        if self.lifecycle in {
            MarketLifecycle.CLOSED,
            MarketLifecycle.EXPIRED,
            MarketLifecycle.SETTLING,
            MarketLifecycle.SETTLED,
        } and self.closes_at is None:
            raise ValueError("closed or later states require closes_at")

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("lineage must belong to UMD")
        if self.lineage.build_id != UMD_008_BUILD_ID:
            raise ValueError("lineage must use build_id UMD-008")

    @classmethod
    def from_market(
        cls,
        market: CertifiedCanonicalMarket,
        *,
        final_value: str | None,
        metadata: Mapping[str, Any],
        lineage: ImmutableLineage,
    ) -> "CertifiedMarketLifecycleSettlementRecord":
        return cls(
            canonical_market_id=market.canonical_market_id,
            lifecycle=market.lifecycle,
            opens_at=market.opens_at,
            closes_at=market.closes_at,
            expires_at=market.expires_at,
            settles_at=market.settles_at,
            settlement_method=market.settlement_method,
            settlement_source=market.settlement_source,
            settlement_rule=market.settlement_rule,
            final_value=final_value,
            metadata=metadata,
            lineage=lineage,
        )

    @property
    def lifecycle_record_id(self) -> str:
        return "umd:lifecycle:" + deterministic_sha256({
            "canonical_market_id": self.canonical_market_id
        })

    def state_payload(self) -> Mapping[str, Any]:
        return {
            "lifecycle": self.lifecycle,
            "opens_at": self.opens_at,
            "closes_at": self.closes_at,
            "expires_at": self.expires_at,
            "settles_at": self.settles_at,
            "settlement_method": self.settlement_method,
            "settlement_source": self.settlement_source,
            "settlement_rule": self.settlement_rule,
            "final_value": self.final_value,
        }

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "lifecycle_record_id": self.lifecycle_record_id,
            "canonical_market_id": self.canonical_market_id,
            **self.state_payload(),
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

    def validate_transition_to(
        self,
        next_record: "CertifiedMarketLifecycleSettlementRecord",
    ) -> bool:
        if self.canonical_market_id != next_record.canonical_market_id:
            raise ValueError("transition must remain on the same market")
        if self.record_hash not in next_record.lineage.parent_hashes:
            raise ValueError("next lineage must include prior record hash")
        if next_record.lifecycle not in ALLOWED_TRANSITIONS[self.lifecycle]:
            raise ValueError(
                f"invalid lifecycle transition: "
                f"{self.lifecycle.value} -> {next_record.lifecycle.value}"
            )
        return True

@dataclass(frozen=True, slots=True)
class ReadOnlyMarketLifecycleSettlementRegistry:
    records: Tuple[CertifiedMarketLifecycleSettlementRecord, ...]
    markets: Tuple[CertifiedCanonicalMarket, ...]
    metadata_registry: ReadOnlyMarketMetadataRegistry
    registry_lineage: ImmutableLineage
    _by_market_id: Mapping[str, CertifiedMarketLifecycleSettlementRecord] = field(
        init=False, repr=False
    )
    _by_record_id: Mapping[str, CertifiedMarketLifecycleSettlementRecord] = field(
        init=False, repr=False
    )

    def __post_init__(self) -> None:
        records = tuple(sorted(self.records, key=lambda x: x.lifecycle_record_id))
        markets = tuple(sorted(self.markets, key=lambda x: x.canonical_market_id))
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "markets", markets)

        if self.registry_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("registry lineage must belong to UMD")
        if self.registry_lineage.build_id != UMD_008_BUILD_ID:
            raise ValueError("registry lineage must use build_id UMD-008")

        market_by_id = {m.canonical_market_id: m for m in markets}
        if len(market_by_id) != len(markets):
            raise ValueError("duplicate canonical market IDs supplied")

        by_market_id = {}
        by_record_id = {}
        for record in records:
            if record.lifecycle_record_id in by_record_id:
                raise ValueError("duplicate lifecycle record ID")
            if record.canonical_market_id in by_market_id:
                raise ValueError("market may have only one current lifecycle record")

            market = market_by_id.get(record.canonical_market_id)
            if market is None:
                raise ValueError("unknown canonical market ID")
            if self.metadata_registry.get_by_market(record.canonical_market_id) is None:
                raise ValueError("lifecycle record requires certified metadata")

            expected = CertifiedMarketLifecycleSettlementRecord.from_market(
                market,
                final_value=record.final_value,
                metadata=record.metadata,
                lineage=record.lineage,
            )
            if record.state_payload() != expected.state_payload():
                raise ValueError(
                    "lifecycle or settlement fields do not match canonical market"
                )

            by_market_id[record.canonical_market_id] = record
            by_record_id[record.lifecycle_record_id] = record

        object.__setattr__(
            self,
            "_by_market_id",
            MappingProxyType(by_market_id),
        )
        object.__setattr__(
            self,
            "_by_record_id",
            MappingProxyType(by_record_id),
        )

    def get_by_market(
        self,
        canonical_market_id: str,
    ) -> CertifiedMarketLifecycleSettlementRecord | None:
        return self._by_market_id.get(
            _text(canonical_market_id, "canonical_market_id")
        )

    def get(
        self,
        lifecycle_record_id: str,
    ) -> CertifiedMarketLifecycleSettlementRecord | None:
        return self._by_record_id.get(
            _text(lifecycle_record_id, "lifecycle_record_id")
        )

    def markets_expiring_by(
        self,
        cutoff: datetime,
    ) -> Tuple[CertifiedMarketLifecycleSettlementRecord, ...]:
        cutoff = _utc(cutoff, "cutoff")
        return tuple(sorted(
            (
                record
                for record in self.records
                if record.expires_at is not None
                and record.expires_at <= cutoff
            ),
            key=lambda x: (x.expires_at, x.canonical_market_id),
        ))

    def missing_lifecycle_market_ids(self) -> Tuple[str, ...]:
        return tuple(
            market.canonical_market_id
            for market in self.markets
            if market.canonical_market_id not in self._by_market_id
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "read_only",
            "records": self.records,
            "market_record_hashes": tuple(
                market.record_hash for market in self.markets
            ),
            "metadata_registry_hash": self.metadata_registry.registry_hash,
            "registry_lineage": self.registry_lineage,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class UMD008CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    registry_mode: str
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
            "network_enabled": self.network_enabled,
            "persistence_enabled": self.persistence_enabled,
            "mutation_enabled": self.mutation_enabled,
            "publication_enabled": self.publication_enabled,
            "execution_enabled": self.execution_enabled,
        }

    @property
    def manifest_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

def build_umd_008_certification_manifest() -> UMD008CertificationManifest:
    return UMD008CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_008_BUILD_ID,
        build_name=UMD_008_BUILD_NAME,
        revision=UMD_008_REVISION,
        schema_version=UMD_008_SCHEMA_VERSION,
        upstream_builds=(
            "UMD-001", "UMD-002", "UMD-003", "UMD-004",
            "UMD-005", "UMD-006", "UMD-007",
        ),
        registry_mode="read_only",
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )

def certify_umd_008_foundation() -> Mapping[str, Any]:
    manifest = build_umd_008_certification_manifest()
    checks = {
        "build_identity": manifest.build_id == "UMD-008",
        "upstreams_frozen": manifest.upstream_builds == (
            "UMD-001", "UMD-002", "UMD-003", "UMD-004",
            "UMD-005", "UMD-006", "UMD-007",
        ),
        "read_only": manifest.registry_mode == "read_only",
        "network_disabled": not manifest.network_enabled,
        "persistence_disabled": not manifest.persistence_enabled,
        "mutation_disabled": not manifest.mutation_enabled,
        "publication_disabled": not manifest.publication_enabled,
        "execution_disabled": not manifest.execution_enabled,
        "deterministic_manifest_hash": manifest.manifest_hash
        == deterministic_sha256(manifest.to_canonical_dict()),
    }
    failed = tuple(name for name, ok in checks.items() if not ok)
    return MappingProxyType({
        "certified": not failed,
        "build_id": manifest.build_id,
        "revision": manifest.revision,
        "manifest_hash": manifest.manifest_hash,
        "checks": MappingProxyType(checks),
        "failed_checks": failed,
    })

def certify_market_lifecycle_and_settlement_registry(
    registry: ReadOnlyMarketLifecycleSettlementRegistry,
    *,
    require_all_markets_tracked: bool = True,
) -> Mapping[str, Any]:
    missing = registry.missing_lifecycle_market_ids()
    checks = {
        "record_ids_unique": len(
            {r.lifecycle_record_id for r in registry.records}
        ) == len(registry.records),
        "market_records_unique": len(
            {r.canonical_market_id for r in registry.records}
        ) == len(registry.records),
        "all_markets_resolve": all(
            registry.get_by_market(r.canonical_market_id) is not None
            for r in registry.records
        ),
        "deterministic_replay": registry.registry_hash
        == deterministic_sha256(registry.to_canonical_dict()),
        "all_markets_tracked": (
            not missing if require_all_markets_tracked else True
        ),
    }
    failed = tuple(name for name, ok in checks.items() if not ok)
    return MappingProxyType({
        "certified": not failed,
        "registry_hash": registry.registry_hash,
        "record_count": len(registry.records),
        "missing_lifecycle_market_ids": missing,
        "checks": MappingProxyType(checks),
        "failed_checks": failed,
    })

def verify_umd_008_certified_market_lifecycle_and_settlement_registry() -> bool:
    result = certify_umd_008_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-008 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True

__all__ = [
    "UMD_008_BUILD_ID",
    "UMD_008_BUILD_NAME",
    "UMD_008_REVISION",
    "UMD_008_SCHEMA_VERSION",
    "ALLOWED_TRANSITIONS",
    "CertifiedMarketLifecycleSettlementRecord",
    "ReadOnlyMarketLifecycleSettlementRegistry",
    "UMD008CertificationManifest",
    "build_umd_008_certification_manifest",
    "certify_market_lifecycle_and_settlement_registry",
    "certify_umd_008_foundation",
    "verify_umd_008_certified_market_lifecycle_and_settlement_registry",
]
