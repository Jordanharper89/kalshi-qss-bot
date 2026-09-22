from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence, Tuple


UMD_SUBSYSTEM_ID = "UMD"
UMD_BUILD_ID = "UMD-001"
UMD_BUILD_NAME = "Universal Market Discovery Foundation"
UMD_REVISION = "UMD_001_UNIVERSAL_MARKET_DISCOVERY_FOUNDATION_V1"
UMD_SCHEMA_VERSION = "1.0.0"

PRIMARY_MISSION = "Observe the real world before financial markets react."

PERMANENT_ARCHITECTURE = (
    "Observation Intelligence",
    "Universal Market Discovery",
    "Oracle Memory",
    "Continuous Learner",
    "Scientific Reasoning",
    "Oracle Operator",
    "Q Series Execution",
)

FROZEN_UPSTREAM_SUBSYSTEMS = (
    "Oracle Terminal (OIT)",
    "Oracle Memory (OML)",
)

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "live_market_scanning",
    "order_creation",
    "order_submission",
    "trade_execution",
    "position_management",
    "publication",
    "runtime_mutation",
    "oracle_memory_mutation",
    "oracle_terminal_mutation",
    "background_workers",
)

FOUNDATION_CAPABILITIES = (
    "canonical_market_identity_contract",
    "venue_abstraction_contract",
    "market_category_contract",
    "market_metadata_contract",
    "expiration_metadata_contract",
    "settlement_metadata_contract",
    "immutable_lineage_contract",
    "deterministic_hashing",
    "deterministic_replay",
    "read_only_certification",
)


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("datetime values must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, (tuple, list)):
        return [_canonicalize(item) for item in value]
    if isinstance(value, (set, frozenset)):
        normalized = [_canonicalize(item) for item in value]
        return sorted(
            normalized,
            key=lambda item: json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ),
        )
    if hasattr(value, "to_canonical_dict"):
        return _canonicalize(value.to_canonical_dict())
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported canonical value type: {type(value)!r}")


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def deterministic_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _require_non_empty_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _normalize_slug(value: str, field_name: str) -> str:
    normalized = _require_non_empty_text(value, field_name).lower()
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    if any(character not in allowed for character in normalized):
        raise ValueError(
            f"{field_name} may contain only lowercase letters, digits, hyphen, and underscore"
        )
    return normalized


def _normalize_symbol(value: str, field_name: str) -> str:
    normalized = _require_non_empty_text(value, field_name).upper()
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-"
    if any(character not in allowed for character in normalized):
        raise ValueError(f"{field_name} contains unsupported characters")
    return normalized


def _normalize_datetime(value: datetime | None, field_name: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime or None")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    copied = {
        _require_non_empty_text(str(key), "metadata key"): _canonicalize(item)
        for key, item in value.items()
    }
    return MappingProxyType(dict(sorted(copied.items())))


class MarketLifecycle(str, Enum):
    UNKNOWN = "unknown"
    ANNOUNCED = "announced"
    OPEN = "open"
    PAUSED = "paused"
    CLOSED = "closed"
    EXPIRED = "expired"
    SETTLING = "settling"
    SETTLED = "settled"
    CANCELLED = "cancelled"


class MarketInstrumentType(str, Enum):
    UNKNOWN = "unknown"
    BINARY = "binary"
    CATEGORICAL = "categorical"
    SCALAR = "scalar"
    RANGE = "range"
    ORDER_BOOK = "order_book"
    AMM = "amm"
    SECURITY = "security"
    SPOT = "spot"
    FUTURE = "future"
    OPTION = "option"
    INDEX = "index"
    OTHER = "other"


class SettlementMethod(str, Enum):
    UNKNOWN = "unknown"
    CASH = "cash"
    PHYSICAL = "physical"
    ORACLE = "oracle"
    VENUE_DETERMINED = "venue_determined"
    THIRD_PARTY_SOURCE = "third_party_source"
    MANUAL_REVIEW = "manual_review"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class ImmutableLineage:
    subsystem_id: str
    build_id: str
    revision: str
    schema_version: str
    parent_hashes: Tuple[str, ...] = field(default_factory=tuple)
    source_refs: Tuple[str, ...] = field(default_factory=tuple)
    created_at: datetime = field(
        default_factory=lambda: datetime(1970, 1, 1, tzinfo=timezone.utc)
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "subsystem_id", _normalize_symbol(self.subsystem_id, "subsystem_id")
        )
        object.__setattr__(self, "build_id", _normalize_symbol(self.build_id, "build_id"))
        object.__setattr__(
            self, "revision", _normalize_symbol(self.revision, "revision")
        )
        object.__setattr__(
            self,
            "schema_version",
            _require_non_empty_text(self.schema_version, "schema_version"),
        )

        normalized_parent_hashes = tuple(
            sorted(
                {
                    _require_non_empty_text(item, "parent_hash")
                    for item in self.parent_hashes
                }
            )
        )
        for item in normalized_parent_hashes:
            if len(item) != 64 or any(ch not in "0123456789abcdef" for ch in item):
                raise ValueError("parent hashes must be lowercase SHA-256 hex digests")
        object.__setattr__(self, "parent_hashes", normalized_parent_hashes)

        normalized_source_refs = tuple(
            sorted(
                {
                    _require_non_empty_text(item, "source_ref")
                    for item in self.source_refs
                }
            )
        )
        object.__setattr__(self, "source_refs", normalized_source_refs)
        object.__setattr__(
            self,
            "created_at",
            _normalize_datetime(self.created_at, "created_at"),
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "subsystem_id": self.subsystem_id,
            "build_id": self.build_id,
            "revision": self.revision,
            "schema_version": self.schema_version,
            "parent_hashes": self.parent_hashes,
            "source_refs": self.source_refs,
            "created_at": self.created_at,
        }

    @property
    def lineage_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class VenueIdentity:
    venue_id: str
    canonical_name: str
    venue_type: str
    jurisdiction: str
    native_market_namespace: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "venue_id", _normalize_slug(self.venue_id, "venue_id"))
        object.__setattr__(
            self,
            "canonical_name",
            _require_non_empty_text(self.canonical_name, "canonical_name"),
        )
        object.__setattr__(
            self, "venue_type", _normalize_slug(self.venue_type, "venue_type")
        )
        object.__setattr__(
            self,
            "jurisdiction",
            _normalize_symbol(self.jurisdiction, "jurisdiction"),
        )
        object.__setattr__(
            self,
            "native_market_namespace",
            _normalize_slug(
                self.native_market_namespace, "native_market_namespace"
            ),
        )
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "venue_id": self.venue_id,
            "canonical_name": self.canonical_name,
            "venue_type": self.venue_type,
            "jurisdiction": self.jurisdiction,
            "native_market_namespace": self.native_market_namespace,
            "metadata": self.metadata,
        }

    @property
    def venue_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class MarketCategory:
    category_id: str
    canonical_name: str
    parent_category_id: str | None = None
    path: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        category_id = _normalize_slug(self.category_id, "category_id")
        object.__setattr__(self, "category_id", category_id)
        object.__setattr__(
            self,
            "canonical_name",
            _require_non_empty_text(self.canonical_name, "canonical_name"),
        )
        if self.parent_category_id is not None:
            parent = _normalize_slug(
                self.parent_category_id, "parent_category_id"
            )
            if parent == category_id:
                raise ValueError("category cannot be its own parent")
            object.__setattr__(self, "parent_category_id", parent)

        normalized_path = tuple(
            _normalize_slug(item, "category path item") for item in self.path
        )
        if normalized_path and normalized_path[-1] != category_id:
            raise ValueError("category path must end with category_id")
        if len(set(normalized_path)) != len(normalized_path):
            raise ValueError("category path must not contain cycles")
        object.__setattr__(self, "path", normalized_path)

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "category_id": self.category_id,
            "canonical_name": self.canonical_name,
            "parent_category_id": self.parent_category_id,
            "path": self.path,
        }

    @property
    def category_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class ExpirationMetadata:
    opens_at: datetime | None = None
    closes_at: datetime | None = None
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        opens_at = _normalize_datetime(self.opens_at, "opens_at")
        closes_at = _normalize_datetime(self.closes_at, "closes_at")
        expires_at = _normalize_datetime(self.expires_at, "expires_at")
        object.__setattr__(self, "opens_at", opens_at)
        object.__setattr__(self, "closes_at", closes_at)
        object.__setattr__(self, "expires_at", expires_at)

        ordered = [item for item in (opens_at, closes_at, expires_at) if item is not None]
        if ordered != sorted(ordered):
            raise ValueError(
                "expiration timestamps must satisfy opens_at <= closes_at <= expires_at"
            )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "opens_at": self.opens_at,
            "closes_at": self.closes_at,
            "expires_at": self.expires_at,
        }


@dataclass(frozen=True, slots=True)
class SettlementMetadata:
    method: SettlementMethod = SettlementMethod.UNKNOWN
    settlement_source: str | None = None
    settlement_rule: str | None = None
    settles_at: datetime | None = None
    final_value: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.method, SettlementMethod):
            object.__setattr__(self, "method", SettlementMethod(self.method))
        if self.settlement_source is not None:
            object.__setattr__(
                self,
                "settlement_source",
                _require_non_empty_text(
                    self.settlement_source, "settlement_source"
                ),
            )
        if self.settlement_rule is not None:
            object.__setattr__(
                self,
                "settlement_rule",
                _require_non_empty_text(self.settlement_rule, "settlement_rule"),
            )
        object.__setattr__(
            self,
            "settles_at",
            _normalize_datetime(self.settles_at, "settles_at"),
        )
        if self.final_value is not None:
            object.__setattr__(
                self,
                "final_value",
                _require_non_empty_text(self.final_value, "final_value"),
            )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "method": self.method,
            "settlement_source": self.settlement_source,
            "settlement_rule": self.settlement_rule,
            "settles_at": self.settles_at,
            "final_value": self.final_value,
        }


@dataclass(frozen=True, slots=True)
class CanonicalMarketIdentity:
    venue: VenueIdentity
    native_market_id: str
    canonical_title: str
    instrument_type: MarketInstrumentType
    category: MarketCategory
    lifecycle: MarketLifecycle
    expiration: ExpirationMetadata
    settlement: SettlementMetadata
    outcome_labels: Tuple[str, ...]
    market_metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "native_market_id",
            _require_non_empty_text(self.native_market_id, "native_market_id"),
        )
        object.__setattr__(
            self,
            "canonical_title",
            _require_non_empty_text(self.canonical_title, "canonical_title"),
        )
        if not isinstance(self.instrument_type, MarketInstrumentType):
            object.__setattr__(
                self,
                "instrument_type",
                MarketInstrumentType(self.instrument_type),
            )
        if not isinstance(self.lifecycle, MarketLifecycle):
            object.__setattr__(self, "lifecycle", MarketLifecycle(self.lifecycle))

        normalized_outcomes = tuple(
            _require_non_empty_text(item, "outcome_label")
            for item in self.outcome_labels
        )
        if len(set(label.casefold() for label in normalized_outcomes)) != len(
            normalized_outcomes
        ):
            raise ValueError("outcome labels must be unique")
        object.__setattr__(self, "outcome_labels", normalized_outcomes)
        object.__setattr__(
            self, "market_metadata", _freeze_mapping(self.market_metadata)
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("market lineage must belong to UMD")
        if self.lineage.build_id != UMD_BUILD_ID:
            raise ValueError("UMD-001 market lineage must use build_id UMD-001")

    def identity_payload(self) -> Mapping[str, Any]:
        return {
            "venue_id": self.venue.venue_id,
            "native_market_namespace": self.venue.native_market_namespace,
            "native_market_id": self.native_market_id,
        }

    @property
    def canonical_market_id(self) -> str:
        digest = deterministic_sha256(self.identity_payload())
        return f"umd:mkt:{digest}"

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "canonical_market_id": self.canonical_market_id,
            "venue": self.venue,
            "native_market_id": self.native_market_id,
            "canonical_title": self.canonical_title,
            "instrument_type": self.instrument_type,
            "category": self.category,
            "lifecycle": self.lifecycle,
            "expiration": self.expiration,
            "settlement": self.settlement,
            "outcome_labels": self.outcome_labels,
            "market_metadata": self.market_metadata,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class ReadOnlyMarketRegistry:
    markets: Tuple[CanonicalMarketIdentity, ...]
    registry_lineage: ImmutableLineage

    def __post_init__(self) -> None:
        ordered = tuple(
            sorted(self.markets, key=lambda item: item.canonical_market_id)
        )
        ids = [item.canonical_market_id for item in ordered]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate canonical market IDs are not allowed")
        native_keys = [
            (
                item.venue.venue_id,
                item.venue.native_market_namespace,
                item.native_market_id,
            )
            for item in ordered
        ]
        if len(native_keys) != len(set(native_keys)):
            raise ValueError("duplicate venue-native market identities are not allowed")
        object.__setattr__(self, "markets", ordered)

        if self.registry_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("registry lineage must belong to UMD")
        if self.registry_lineage.build_id != UMD_BUILD_ID:
            raise ValueError("UMD-001 registry lineage must use build_id UMD-001")

    def get(self, canonical_market_id: str) -> CanonicalMarketIdentity | None:
        requested = _require_non_empty_text(
            canonical_market_id, "canonical_market_id"
        )
        for market in self.markets:
            if market.canonical_market_id == requested:
                return market
        return None

    def by_venue(self, venue_id: str) -> Tuple[CanonicalMarketIdentity, ...]:
        normalized = _normalize_slug(venue_id, "venue_id")
        return tuple(
            market for market in self.markets if market.venue.venue_id == normalized
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "read_only",
            "markets": self.markets,
            "registry_lineage": self.registry_lineage,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class UMDFoundationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    primary_mission: str
    permanent_architecture: Tuple[str, ...]
    frozen_upstream_subsystems: Tuple[str, ...]
    capabilities: Tuple[str, ...]
    prohibited_capabilities: Tuple[str, ...]
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
            "primary_mission": self.primary_mission,
            "permanent_architecture": self.permanent_architecture,
            "frozen_upstream_subsystems": self.frozen_upstream_subsystems,
            "capabilities": self.capabilities,
            "prohibited_capabilities": self.prohibited_capabilities,
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


def build_umd_foundation_manifest() -> UMDFoundationManifest:
    return UMDFoundationManifest(
        subsystem_id=UMD_SUBSYSTEM_ID,
        build_id=UMD_BUILD_ID,
        build_name=UMD_BUILD_NAME,
        revision=UMD_REVISION,
        schema_version=UMD_SCHEMA_VERSION,
        primary_mission=PRIMARY_MISSION,
        permanent_architecture=PERMANENT_ARCHITECTURE,
        frozen_upstream_subsystems=FROZEN_UPSTREAM_SUBSYSTEMS,
        capabilities=FOUNDATION_CAPABILITIES,
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        registry_mode="read_only",
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_foundation(
    manifest: UMDFoundationManifest | None = None,
) -> Mapping[str, Any]:
    active_manifest = manifest or build_umd_foundation_manifest()

    checks = {
        "subsystem_identity": active_manifest.subsystem_id == "UMD",
        "build_identity": active_manifest.build_id == "UMD-001",
        "mission_preserved": active_manifest.primary_mission == PRIMARY_MISSION,
        "architecture_preserved": (
            active_manifest.permanent_architecture == PERMANENT_ARCHITECTURE
        ),
        "upstream_frozen": (
            active_manifest.frozen_upstream_subsystems
            == FROZEN_UPSTREAM_SUBSYSTEMS
        ),
        "read_only_registry": active_manifest.registry_mode == "read_only",
        "network_disabled": active_manifest.network_enabled is False,
        "persistence_disabled": active_manifest.persistence_enabled is False,
        "mutation_disabled": active_manifest.mutation_enabled is False,
        "publication_disabled": active_manifest.publication_enabled is False,
        "execution_disabled": active_manifest.execution_enabled is False,
        "required_capabilities_present": set(FOUNDATION_CAPABILITIES).issubset(
            active_manifest.capabilities
        ),
        "prohibited_capabilities_declared": set(PROHIBITED_CAPABILITIES).issubset(
            active_manifest.prohibited_capabilities
        ),
        "deterministic_manifest_hash": (
            active_manifest.manifest_hash
            == deterministic_sha256(active_manifest.to_canonical_dict())
        ),
    }

    failed = tuple(name for name, passed in checks.items() if not passed)
    result = {
        "certified": not failed,
        "build_id": active_manifest.build_id,
        "revision": active_manifest.revision,
        "manifest_hash": active_manifest.manifest_hash,
        "checks": checks,
        "failed_checks": failed,
    }
    return MappingProxyType(result)


def verify_umd_foundation() -> bool:
    certification = certify_umd_foundation()
    if not certification["certified"]:
        raise RuntimeError(
            "UMD-001 foundation certification failed: "
            + ", ".join(certification["failed_checks"])
        )
    return True


__all__ = [
    "UMD_SUBSYSTEM_ID",
    "UMD_BUILD_ID",
    "UMD_BUILD_NAME",
    "UMD_REVISION",
    "UMD_SCHEMA_VERSION",
    "PRIMARY_MISSION",
    "PERMANENT_ARCHITECTURE",
    "FROZEN_UPSTREAM_SUBSYSTEMS",
    "PROHIBITED_CAPABILITIES",
    "FOUNDATION_CAPABILITIES",
    "MarketLifecycle",
    "MarketInstrumentType",
    "SettlementMethod",
    "ImmutableLineage",
    "VenueIdentity",
    "MarketCategory",
    "ExpirationMetadata",
    "SettlementMetadata",
    "CanonicalMarketIdentity",
    "ReadOnlyMarketRegistry",
    "UMDFoundationManifest",
    "canonical_json",
    "deterministic_sha256",
    "build_umd_foundation_manifest",
    "certify_umd_foundation",
    "verify_umd_foundation",
]
