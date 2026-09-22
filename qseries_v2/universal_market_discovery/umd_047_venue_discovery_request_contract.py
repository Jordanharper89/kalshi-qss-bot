from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_045_venue_discovery_source_contract import CertifiedVenueDiscoverySourceContract
from .umd_046_venue_discovery_source_registry import CertifiedVenueDiscoverySourceRegistry

UMD_047_BUILD_ID = "UMD-047"
UMD_047_BUILD_NAME = "Certified Venue Discovery Request Contract"
UMD_047_REVISION = "UMD_047_CERTIFIED_VENUE_DISCOVERY_REQUEST_CONTRACT_V1"
UMD_047_SCHEMA_VERSION = "1.0.0"
ALLOWED_DISCOVERY_SCOPES = ("ACTIVE_ONLY", "HISTORICAL_ONLY", "ACTIVE_AND_HISTORICAL", "STATUS_FILTERED")
PROHIBITED_CAPABILITIES = (
    "network_invocation", "authentication_execution", "credential_storage",
    "automatic_discovery", "automatic_pagination", "registry_mutation",
    "request_persistence", "publication", "order_submission", "trade_execution",
)

def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str): raise TypeError(f"{field_name} must be a string")
    value = " ".join(value.strip().split())
    if not value: raise ValueError(f"{field_name} must not be empty")
    return value

def _token(value: str, field_name: str) -> str:
    value = _text(value, field_name).upper().replace("-", "_")
    if not all(ch.isalnum() or ch == "_" for ch in value):
        raise ValueError(f"{field_name} contains invalid characters")
    return value

def _sha256(value: str, field_name: str) -> str:
    value = _text(value, field_name).lower()
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256 hexadecimal")
    return value

def _utc(value: datetime | None, field_name: str) -> datetime | None:
    if value is None: return None
    if not isinstance(value, datetime): raise TypeError(f"{field_name} must be a datetime or None")
    if value.tzinfo is None: raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)

def _tokens(values: Tuple[str, ...], field_name: str) -> Tuple[str, ...]:
    if not isinstance(values, tuple): values = tuple(values)
    return tuple(sorted({_token(v, field_name) for v in values}))

def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping): raise TypeError("metadata must be a mapping")
    return MappingProxyType(dict(sorted((str(k), v) for k, v in value.items())))

@dataclass(frozen=True, slots=True)
class CertifiedVenueDiscoveryRequestContract:
    source_id: str
    source_contract_hash: str
    source_registry_hash: str
    canonical_venue_id: str
    adapter_key: str
    discovery_scope: str
    requested_statuses: Tuple[str, ...]
    requested_market_families: Tuple[str, ...]
    window_start: datetime | None
    window_end: datetime | None
    pagination_cursor: str | None
    page_size: int | None
    requested_at: datetime
    request_schema_version: str
    read_only: bool
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _text(self.source_id, "source_id"))
        object.__setattr__(self, "source_contract_hash", _sha256(self.source_contract_hash, "source_contract_hash"))
        object.__setattr__(self, "source_registry_hash", _sha256(self.source_registry_hash, "source_registry_hash"))
        object.__setattr__(self, "canonical_venue_id", _token(self.canonical_venue_id, "canonical_venue_id"))
        object.__setattr__(self, "adapter_key", _token(self.adapter_key, "adapter_key"))
        scope = _token(self.discovery_scope, "discovery_scope")
        if scope not in ALLOWED_DISCOVERY_SCOPES: raise ValueError("discovery_scope is not certified")
        object.__setattr__(self, "discovery_scope", scope)
        object.__setattr__(self, "requested_statuses", _tokens(self.requested_statuses, "requested_status"))
        object.__setattr__(self, "requested_market_families", _tokens(self.requested_market_families, "requested_market_family"))
        object.__setattr__(self, "window_start", _utc(self.window_start, "window_start"))
        object.__setattr__(self, "window_end", _utc(self.window_end, "window_end"))
        if self.window_start is not None and self.window_end is not None and self.window_end < self.window_start:
            raise ValueError("window_end must not precede window_start")
        if self.pagination_cursor is not None:
            object.__setattr__(self, "pagination_cursor", _text(self.pagination_cursor, "pagination_cursor"))
        if self.page_size is not None:
            if not isinstance(self.page_size, int): raise TypeError("page_size must be an integer or None")
            if self.page_size < 1 or self.page_size > 10000: raise ValueError("page_size must be between 1 and 10000")
        object.__setattr__(self, "requested_at", _utc(self.requested_at, "requested_at"))
        object.__setattr__(self, "request_schema_version", _text(self.request_schema_version, "request_schema_version"))
        if self.read_only is not True: raise ValueError("discovery requests must be read-only")
        object.__setattr__(self, "metadata", _freeze(self.metadata))
        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID: raise ValueError("request lineage must belong to UMD")
        if self.lineage.build_id != UMD_047_BUILD_ID: raise ValueError("request lineage must use build_id UMD-047")
        required = {self.source_contract_hash, self.source_registry_hash}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("request lineage must include source contract and registry hashes")

    @property
    def request_id(self) -> str:
        return "umd:venue-discovery-request:" + deterministic_sha256({
            "source_id": self.source_id, "source_contract_hash": self.source_contract_hash,
            "source_registry_hash": self.source_registry_hash, "discovery_scope": self.discovery_scope,
            "requested_statuses": self.requested_statuses, "requested_market_families": self.requested_market_families,
            "window_start": self.window_start, "window_end": self.window_end,
            "pagination_cursor": self.pagination_cursor, "page_size": self.page_size,
            "requested_at": self.requested_at, "request_schema_version": self.request_schema_version,
        })

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "request_id": self.request_id, "source_id": self.source_id,
            "source_contract_hash": self.source_contract_hash, "source_registry_hash": self.source_registry_hash,
            "canonical_venue_id": self.canonical_venue_id, "adapter_key": self.adapter_key,
            "discovery_scope": self.discovery_scope, "requested_statuses": self.requested_statuses,
            "requested_market_families": self.requested_market_families,
            "window_start": self.window_start, "window_end": self.window_end,
            "pagination_cursor": self.pagination_cursor, "page_size": self.page_size,
            "requested_at": self.requested_at, "request_schema_version": self.request_schema_version,
            "read_only": self.read_only, "metadata": self.metadata, "lineage": self.lineage,
        }

    @property
    def request_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


def build_venue_discovery_request_contract(
    registry: CertifiedVenueDiscoverySourceRegistry,
    source: CertifiedVenueDiscoverySourceContract,
    *, discovery_scope: str, requested_statuses: Tuple[str, ...],
    requested_market_families: Tuple[str, ...], requested_at: datetime,
    request_schema_version: str, lineage: ImmutableLineage,
    window_start: datetime | None = None, window_end: datetime | None = None,
    pagination_cursor: str | None = None, page_size: int | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> CertifiedVenueDiscoveryRequestContract:
    if not isinstance(registry, CertifiedVenueDiscoverySourceRegistry): raise TypeError("registry must be certified UMD-046")
    if not isinstance(source, CertifiedVenueDiscoverySourceContract): raise TypeError("source must be certified UMD-045")
    registered = registry.get(source.source_id)
    if registered is None or registered.contract_hash != source.contract_hash:
        raise ValueError("source is not registered in the supplied UMD-046 registry")
    statuses = _tokens(requested_statuses, "requested_status")
    families = _tokens(requested_market_families, "requested_market_family")
    if not set(statuses).issubset(set(source.supported_statuses)):
        raise ValueError("requested statuses exceed source capabilities")
    if not set(families).issubset(set(source.supported_market_families)):
        raise ValueError("requested market families exceed source capabilities")
    if pagination_cursor is not None and source.pagination_mode not in ("CURSOR", "TOKEN"):
        raise ValueError("pagination cursor is incompatible with source pagination mode")
    if discovery_scope in ("HISTORICAL_ONLY", "ACTIVE_AND_HISTORICAL") and not source.supports_historical_markets:
        raise ValueError("source does not support historical market discovery")
    return CertifiedVenueDiscoveryRequestContract(
        source_id=source.source_id, source_contract_hash=source.contract_hash,
        source_registry_hash=registry.registry_hash, canonical_venue_id=source.canonical_venue_id,
        adapter_key=source.adapter_key, discovery_scope=discovery_scope,
        requested_statuses=statuses, requested_market_families=families,
        window_start=window_start, window_end=window_end, pagination_cursor=pagination_cursor,
        page_size=page_size, requested_at=requested_at, request_schema_version=request_schema_version,
        read_only=True, metadata={} if metadata is None else metadata, lineage=lineage,
    )

@dataclass(frozen=True, slots=True)
class UMD047CertificationManifest:
    subsystem_id: str; build_id: str; revision: str; schema_version: str
    upstream_builds: Tuple[str, ...]; contract_mode: str; prohibited_capabilities: Tuple[str, ...]
    network_enabled: bool; persistence_enabled: bool; mutation_enabled: bool; publication_enabled: bool; execution_enabled: bool
    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}
    @property
    def manifest_hash(self) -> str: return deterministic_sha256(self.to_canonical_dict())

def build_umd_047_certification_manifest() -> UMD047CertificationManifest:
    return UMD047CertificationManifest("UMD", UMD_047_BUILD_ID, UMD_047_REVISION, UMD_047_SCHEMA_VERSION,
        tuple(f"UMD-{n:03d}" for n in range(1,47)), "deterministic_read_only_request_definition",
        PROHIBITED_CAPABILITIES, False, False, False, False, False)

def certify_venue_discovery_request_contract(request: CertifiedVenueDiscoveryRequestContract) -> Mapping[str, Any]:
    if not isinstance(request, CertifiedVenueDiscoveryRequestContract): raise TypeError("request must be certified UMD-047")
    checks = {
        "deterministic_request_hash": request.request_hash == deterministic_sha256(request.to_canonical_dict()),
        "lineage_bound": {request.source_contract_hash, request.source_registry_hash}.issubset(set(request.lineage.parent_hashes)),
        "read_only_required": request.read_only is True, "network_not_invoked": True,
    }
    failed=tuple(k for k,v in checks.items() if not v)
    return MappingProxyType({"certified":not failed,"request_id":request.request_id,"request_hash":request.request_hash,
        "source_id":request.source_id,"checks":MappingProxyType(checks),"failed_checks":failed})

def certify_umd_047_foundation() -> Mapping[str, Any]:
    m=build_umd_047_certification_manifest()
    checks={"subsystem_identity":m.subsystem_id=="UMD","build_identity":m.build_id=="UMD-047",
        "upstreams_frozen":m.upstream_builds==tuple(f"UMD-{n:03d}" for n in range(1,47)),
        "request_mode":m.contract_mode=="deterministic_read_only_request_definition",
        "network_disabled":not m.network_enabled,"persistence_disabled":not m.persistence_enabled,
        "mutation_disabled":not m.mutation_enabled,"publication_disabled":not m.publication_enabled,
        "execution_disabled":not m.execution_enabled,"deterministic_manifest":m.manifest_hash==deterministic_sha256(m.to_canonical_dict())}
    failed=tuple(k for k,v in checks.items() if not v)
    return MappingProxyType({"certified":not failed,"build_id":m.build_id,"revision":m.revision,"manifest_hash":m.manifest_hash,
        "checks":MappingProxyType(checks),"failed_checks":failed})

def verify_umd_047_venue_discovery_request_contract() -> bool:
    result=certify_umd_047_foundation()
    if not result["certified"]: raise RuntimeError("UMD-047 foundation certification failed: "+", ".join(result["failed_checks"]))
    return True
