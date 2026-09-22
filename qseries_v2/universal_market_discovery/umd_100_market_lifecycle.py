from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_095_market_identity import CanonicalMarketIdentity
from .umd_099_market_alias_resolution import verify_umd_099_market_alias_resolution

UMD_100_BUILD_ID="UMD-100"
UMD_100_BUILD_NAME="Market Lifecycle Semantics"
UMD_100_REVISION="UMD_100_MARKET_LIFECYCLE_SEMANTICS_V1"
UMD_100_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")
LIFECYCLE_PHASES=("unscheduled","pre_close","post_close_pre_settlement","post_settlement")


def _freeze(value:Mapping[str,Any] | None)->Mapping[str,Any]:
    if value is None: value={}
    if not isinstance(value,Mapping): raise TypeError("metadata must be a mapping")
    return MappingProxyType(dict(sorted((str(k),v) for k,v in value.items())))


def _parse_time(value:str, field_name:str)->datetime | None:
    if not isinstance(value,str): raise TypeError(f"{field_name} must be a string")
    value=value.strip()
    if not value: return None
    if value.endswith("Z"): value=value[:-1]+"+00:00"
    try: dt=datetime.fromisoformat(value)
    except ValueError as exc: raise ValueError(f"{field_name} must be ISO-8601") from exc
    if dt.tzinfo is None or dt.utcoffset() is None: raise ValueError(f"{field_name} must include a timezone")
    return dt.astimezone(timezone.utc)


def _as_utc(value:datetime)->datetime:
    if not isinstance(value,datetime): raise TypeError("as_of must be datetime")
    if value.tzinfo is None or value.utcoffset() is None: raise ValueError("as_of must include a timezone")
    return value.astimezone(timezone.utc)


def _iso(dt:datetime | None)->str:
    return "" if dt is None else dt.isoformat().replace("+00:00","Z")


@dataclass(frozen=True,slots=True)
class MarketLifecycle:
    canonical_market_id:str
    identity_hash:str
    close_at:str
    settlement_at:str
    as_of:str
    scheduled_phase:str
    metadata:Mapping[str,Any]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"metadata",_freeze(self.metadata))
        if self.scheduled_phase not in LIFECYCLE_PHASES: raise ValueError("unsupported scheduled_phase")
        close=_parse_time(self.close_at,"close_at"); settle=_parse_time(self.settlement_at,"settlement_at"); observed=_parse_time(self.as_of,"as_of")
        if observed is None: raise ValueError("as_of must be non-empty")
        if close is not None and settle is not None and settle < close: raise ValueError("settlement_at cannot precede close_at")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_100_BUILD_ID: raise ValueError("lineage must belong to UMD-100")
        if self.identity_hash not in self.lineage.parent_hashes: raise ValueError("lineage must include identity hash")

    def to_canonical_dict(self):
        return {"canonical_market_id":self.canonical_market_id,"identity_hash":self.identity_hash,"close_at":self.close_at,
                "settlement_at":self.settlement_at,"as_of":self.as_of,"scheduled_phase":self.scheduled_phase,
                "metadata":self.metadata,"lineage":self.lineage}

    @property
    def lifecycle_hash(self): return deterministic_sha256(self.to_canonical_dict())


class MarketLifecycleResolver:
    __slots__=()

    def resolve(self,identity:CanonicalMarketIdentity,*,as_of:datetime,lineage:ImmutableLineage,metadata:Mapping[str,Any] | None=None)->MarketLifecycle:
        if not isinstance(identity,CanonicalMarketIdentity): raise TypeError("identity must be CanonicalMarketIdentity")
        observed=_as_utc(as_of)
        close=_parse_time(identity.close_time,"close_time")
        settle=_parse_time(identity.settlement_time,"settlement_time")
        if close is not None and settle is not None and settle < close: raise ValueError("settlement_time cannot precede close_time")
        if close is None and settle is None: phase="unscheduled"
        elif close is None:
            phase="post_settlement" if observed >= settle else "pre_close"
        elif observed < close: phase="pre_close"
        elif settle is None or observed < settle: phase="post_close_pre_settlement"
        else: phase="post_settlement"
        return MarketLifecycle(canonical_market_id=identity.canonical_market_id,identity_hash=identity.identity_hash,
            close_at=_iso(close),settlement_at=_iso(settle),as_of=_iso(observed),scheduled_phase=phase,
            metadata={} if metadata is None else metadata,lineage=lineage)


def build_umd_100_certification_manifest():
    data={"subsystem_id":"UMD","build_id":UMD_100_BUILD_ID,"revision":UMD_100_REVISION,"schema_version":UMD_100_SCHEMA_VERSION,
          "upstream_builds":("UMD-095","UMD-099"),"mode":"deterministic_read_only_market_lifecycle_semantics",
          "lifecycle_phases":LIFECYCLE_PHASES,"prohibited_capabilities":PROHIBITED_CAPABILITIES,
          "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})


def verify_umd_100_market_lifecycle_semantics()->bool:
    if verify_umd_099_market_alias_resolution() is not True: return False
    m=build_umd_100_certification_manifest()
    return m["build_id"]=="UMD-100" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))
