from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_095_market_identity import CanonicalMarketIdentity
from .umd_098_market_taxonomy import MarketTaxonomyClassification, verify_umd_098_market_taxonomy_classification

UMD_099_BUILD_ID="UMD-099"
UMD_099_BUILD_NAME="Market Alias Resolution"
UMD_099_REVISION="UMD_099_MARKET_ALIAS_RESOLUTION_V1"
UMD_099_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")
_WS=re.compile(r"\s+")
_PUNCT=re.compile(r"[^a-z0-9]+")


def normalize_alias(value:str)->str:
    if not isinstance(value,str):
        raise TypeError("alias must be a string")
    value=unicodedata.normalize("NFKC",value)
    value=_WS.sub(" ",value.strip()).casefold()
    key=_PUNCT.sub("-",value).strip("-")
    if not key:
        raise ValueError("alias must contain letters or digits")
    return key


def _freeze(value:Mapping[str,Any] | None)->Mapping[str,Any]:
    if value is None:
        value={}
    if not isinstance(value,Mapping):
        raise TypeError("metadata must be a mapping")
    return MappingProxyType(dict(sorted((str(k),v) for k,v in value.items())))


@dataclass(frozen=True,slots=True)
class AliasBinding:
    alias:str
    alias_key:str
    canonical_market_id:str
    identity_hash:str
    taxonomy_key:str
    source_ref:str
    metadata:Mapping[str,Any]
    lineage:ImmutableLineage

    def __post_init__(self):
        if normalize_alias(self.alias)!=self.alias_key:
            raise ValueError("alias_key does not match alias")
        if not isinstance(self.source_ref,str) or not self.source_ref:
            raise ValueError("source_ref must be non-empty")
        object.__setattr__(self,"metadata",_freeze(self.metadata))
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_099_BUILD_ID:
            raise ValueError("lineage must belong to UMD-099")
        if self.identity_hash not in self.lineage.parent_hashes:
            raise ValueError("lineage must include identity hash")

    def to_canonical_dict(self):
        return {
            "alias":self.alias,
            "alias_key":self.alias_key,
            "canonical_market_id":self.canonical_market_id,
            "identity_hash":self.identity_hash,
            "taxonomy_key":self.taxonomy_key,
            "source_ref":self.source_ref,
            "metadata":self.metadata,
            "lineage":self.lineage,
        }

    @property
    def binding_hash(self):
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True,slots=True)
class AliasIndex:
    bindings:Tuple[AliasBinding,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"bindings",tuple(self.bindings))
        keys={}
        for b in self.bindings:
            previous=keys.get(b.alias_key)
            if previous is not None and previous!=b.canonical_market_id:
                raise ValueError("alias conflict across canonical markets")
            keys[b.alias_key]=b.canonical_market_id
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_099_BUILD_ID:
            raise ValueError("index lineage must belong to UMD-099")

    def resolve(self,alias:str)->str | None:
        key=normalize_alias(alias)
        for b in self.bindings:
            if b.alias_key==key:
                return b.canonical_market_id
        return None

    def to_canonical_dict(self):
        return {"binding_hashes":tuple(b.binding_hash for b in self.bindings),"lineage":self.lineage}

    @property
    def index_hash(self):
        return deterministic_sha256(self.to_canonical_dict())


class MarketAliasResolver:
    __slots__=()

    def build_index(
        self,
        entries:Iterable[tuple[CanonicalMarketIdentity,MarketTaxonomyClassification,Iterable[str],str]],
        *,
        lineage:ImmutableLineage,
    )->AliasIndex:
        bindings=[]
        required=set()
        seen_same=set()
        for identity,classification,aliases,source_ref in entries:
            if not isinstance(identity,CanonicalMarketIdentity):
                raise TypeError("entry identity must be CanonicalMarketIdentity")
            if not isinstance(classification,MarketTaxonomyClassification):
                raise TypeError("entry classification must be MarketTaxonomyClassification")
            if classification.canonical_market_id!=identity.canonical_market_id or classification.identity_hash!=identity.identity_hash:
                raise ValueError("classification does not belong to identity")
            if not isinstance(source_ref,str) or not source_ref:
                raise ValueError("source_ref must be non-empty")
            required.add(identity.identity_hash)
            for alias in aliases:
                key=normalize_alias(alias)
                same_key=(identity.canonical_market_id,key)
                if same_key in seen_same:
                    continue
                seen_same.add(same_key)
                bindings.append(AliasBinding(
                    alias=alias.strip(),
                    alias_key=key,
                    canonical_market_id=identity.canonical_market_id,
                    identity_hash=identity.identity_hash,
                    taxonomy_key=classification.taxonomy_path.taxonomy_key,
                    source_ref=source_ref,
                    metadata={},
                    lineage=lineage,
                ))
        if not required.issubset(set(lineage.parent_hashes)):
            raise ValueError("lineage must include every identity hash")
        bindings.sort(key=lambda b:(b.alias_key,b.canonical_market_id,b.source_ref,b.binding_hash))
        return AliasIndex(bindings=tuple(bindings),lineage=lineage)


def build_umd_099_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_099_BUILD_ID,"revision":UMD_099_REVISION,
        "schema_version":UMD_099_SCHEMA_VERSION,"upstream_builds":("UMD-095","UMD-098"),
        "mode":"deterministic_read_only_alias_resolution",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})


def verify_umd_099_market_alias_resolution()->bool:
    if verify_umd_098_market_taxonomy_classification() is not True:
        return False
    m=build_umd_099_certification_manifest()
    return m["build_id"]=="UMD-099" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
