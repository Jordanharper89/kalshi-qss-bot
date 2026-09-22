from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_095_market_identity import CanonicalMarketIdentity
from .umd_100_market_lifecycle import verify_umd_100_market_lifecycle_semantics

UMD_101_BUILD_ID="UMD-101"
UMD_101_BUILD_NAME="Outcome Schema Resolution"
UMD_101_REVISION="UMD_101_OUTCOME_SCHEMA_RESOLUTION_V1"
UMD_101_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")
SCHEMA_TYPES=("unspecified","binary_yes_no","binary_generic","categorical")


def _freeze(value:Mapping[str,Any] | None)->Mapping[str,Any]:
    if value is None: value={}
    if not isinstance(value,Mapping): raise TypeError("metadata must be a mapping")
    return MappingProxyType(dict(sorted((str(k),v) for k,v in value.items())))


@dataclass(frozen=True,slots=True)
class OutcomeOption:
    outcome_id:str
    outcome_key:str
    ordinal:int

    def __post_init__(self):
        if not isinstance(self.outcome_key,str) or not self.outcome_key: raise ValueError("outcome_key must be non-empty")
        if not isinstance(self.ordinal,int) or self.ordinal<0: raise ValueError("ordinal must be non-negative")
        expected="umd:outcome:"+deterministic_sha256({"outcome_key":self.outcome_key})
        if self.outcome_id!=expected: raise ValueError("outcome_id does not match outcome_key")

    def to_canonical_dict(self): return {"outcome_id":self.outcome_id,"outcome_key":self.outcome_key,"ordinal":self.ordinal}
    @property
    def option_hash(self): return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True,slots=True)
class OutcomeSchema:
    canonical_market_id:str
    identity_hash:str
    schema_type:str
    options:Tuple[OutcomeOption,...]
    metadata:Mapping[str,Any]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"options",tuple(self.options)); object.__setattr__(self,"metadata",_freeze(self.metadata))
        if self.schema_type not in SCHEMA_TYPES: raise ValueError("unsupported schema_type")
        if len({x.outcome_key for x in self.options})!=len(self.options): raise ValueError("outcome keys must be unique")
        if tuple(x.ordinal for x in self.options)!=tuple(range(len(self.options))): raise ValueError("outcome ordinals must be contiguous")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_101_BUILD_ID: raise ValueError("lineage must belong to UMD-101")
        if self.identity_hash not in self.lineage.parent_hashes: raise ValueError("lineage must include identity hash")

    def to_canonical_dict(self):
        return {"canonical_market_id":self.canonical_market_id,"identity_hash":self.identity_hash,"schema_type":self.schema_type,
                "option_hashes":tuple(x.option_hash for x in self.options),"metadata":self.metadata,"lineage":self.lineage}
    @property
    def outcome_schema_hash(self): return deterministic_sha256(self.to_canonical_dict())


class OutcomeSchemaResolver:
    __slots__=()
    def resolve(self,identity:CanonicalMarketIdentity,*,lineage:ImmutableLineage,metadata:Mapping[str,Any] | None=None)->OutcomeSchema:
        if not isinstance(identity,CanonicalMarketIdentity): raise TypeError("identity must be CanonicalMarketIdentity")
        keys=tuple(identity.outcome_keys)
        if len(set(keys))!=len(keys): raise ValueError("identity outcome keys must be unique")
        keyset=set(keys)
        if not keys: schema_type="unspecified"; ordered=()
        elif keyset=={"yes","no"} and len(keys)==2: schema_type="binary_yes_no"; ordered=("yes","no")
        elif len(keys)==2: schema_type="binary_generic"; ordered=tuple(sorted(keys))
        else: schema_type="categorical"; ordered=tuple(sorted(keys))
        options=tuple(OutcomeOption("umd:outcome:"+deterministic_sha256({"outcome_key":key}),key,n) for n,key in enumerate(ordered))
        return OutcomeSchema(canonical_market_id=identity.canonical_market_id,identity_hash=identity.identity_hash,schema_type=schema_type,
            options=options,metadata={} if metadata is None else metadata,lineage=lineage)


def build_umd_101_certification_manifest():
    data={"subsystem_id":"UMD","build_id":UMD_101_BUILD_ID,"revision":UMD_101_REVISION,"schema_version":UMD_101_SCHEMA_VERSION,
          "upstream_builds":("UMD-095","UMD-100"),"mode":"deterministic_read_only_outcome_schema_resolution",
          "schema_types":SCHEMA_TYPES,"prohibited_capabilities":PROHIBITED_CAPABILITIES,
          "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})


def verify_umd_101_outcome_schema_resolution()->bool:
    if verify_umd_100_market_lifecycle_semantics() is not True: return False
    m=build_umd_101_certification_manifest()
    return m["build_id"]=="UMD-101" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))
