from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_095_market_identity import CanonicalMarketIdentity
from .umd_097_market_relationship_graph import verify_umd_097_market_relationship_graph

UMD_098_BUILD_ID="UMD-098"
UMD_098_BUILD_NAME="Market Taxonomy Classification"
UMD_098_REVISION="UMD_098_MARKET_TAXONOMY_CLASSIFICATION_V1"
UMD_098_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")


def _token(value:str,field_name:str)->str:
    if not isinstance(value,str):
        raise TypeError(f"{field_name} must be a string")
    value=value.strip().casefold().replace("_","-").replace(" ","-")
    while "--" in value:
        value=value.replace("--","-")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if any(not (c.isalnum() or c=="-") for c in value):
        raise ValueError(f"{field_name} contains unsupported characters")
    return value


def _freeze(value:Mapping[str,Any] | None)->Mapping[str,Any]:
    if value is None:
        value={}
    if not isinstance(value,Mapping):
        raise TypeError("metadata must be a mapping")
    return MappingProxyType(dict(sorted((str(k),v) for k,v in value.items())))


@dataclass(frozen=True,slots=True)
class TaxonomyPath:
    asset:str
    domain:str
    category:str
    subcategory:str
    market_type:str

    def __post_init__(self):
        for name in ("asset","domain","category","subcategory","market_type"):
            object.__setattr__(self,name,_token(getattr(self,name),name))

    @property
    def taxonomy_key(self)->str:
        return "/".join((self.asset,self.domain,self.category,self.subcategory,self.market_type))


@dataclass(frozen=True,slots=True)
class TaxonomyRule:
    rule_id:str
    path:TaxonomyPath
    category_keys:Tuple[str,...]=()
    title_terms:Tuple[str,...]=()
    priority:int=100

    def __post_init__(self):
        object.__setattr__(self,"rule_id",_token(self.rule_id,"rule_id"))
        if not isinstance(self.path,TaxonomyPath):
            raise TypeError("path must be TaxonomyPath")
        categories=tuple(sorted({_token(x,"category_key") for x in self.category_keys}))
        terms=tuple(sorted({_token(x,"title_term") for x in self.title_terms}))
        if not categories and not terms:
            raise ValueError("taxonomy rule requires category_keys or title_terms")
        if not isinstance(self.priority,int) or self.priority<0:
            raise ValueError("priority must be a non-negative integer")
        object.__setattr__(self,"category_keys",categories)
        object.__setattr__(self,"title_terms",terms)

    def matches(self,identity:CanonicalMarketIdentity)->bool:
        if self.category_keys and identity.category_key in self.category_keys:
            return True
        title_tokens=set(identity.title_key.split("-"))
        return bool(self.title_terms and set(self.title_terms).issubset(title_tokens))


@dataclass(frozen=True,slots=True)
class MarketTaxonomyClassification:
    canonical_market_id:str
    identity_hash:str
    taxonomy_path:TaxonomyPath
    rule_id:str
    metadata:Mapping[str,Any]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"metadata",_freeze(self.metadata))
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_098_BUILD_ID:
            raise ValueError("lineage must belong to UMD-098")
        if self.identity_hash not in self.lineage.parent_hashes:
            raise ValueError("lineage must include identity hash")

    def to_canonical_dict(self):
        return {
            "canonical_market_id":self.canonical_market_id,
            "identity_hash":self.identity_hash,
            "taxonomy_key":self.taxonomy_path.taxonomy_key,
            "rule_id":self.rule_id,
            "metadata":self.metadata,
            "lineage":self.lineage,
        }

    @property
    def classification_hash(self):
        return deterministic_sha256(self.to_canonical_dict())


class MarketTaxonomyClassifier:
    __slots__=("rules",)

    def __init__(self,rules:Iterable[TaxonomyRule]):
        values=tuple(rules)
        if not values:
            raise ValueError("at least one taxonomy rule is required")
        if any(not isinstance(x,TaxonomyRule) for x in values):
            raise TypeError("rules must contain TaxonomyRule")
        if len({x.rule_id for x in values})!=len(values):
            raise ValueError("rule_id values must be unique")
        self.rules=tuple(sorted(values,key=lambda x:(x.priority,x.rule_id)))

    def classify(
        self,
        identity:CanonicalMarketIdentity,
        *,
        lineage:ImmutableLineage,
        metadata:Mapping[str,Any] | None=None,
    )->MarketTaxonomyClassification:
        if not isinstance(identity,CanonicalMarketIdentity):
            raise TypeError("identity must be CanonicalMarketIdentity")
        matches=[rule for rule in self.rules if rule.matches(identity)]
        if not matches:
            raise LookupError("no taxonomy rule matched market identity")
        chosen=matches[0]
        return MarketTaxonomyClassification(
            canonical_market_id=identity.canonical_market_id,
            identity_hash=identity.identity_hash,
            taxonomy_path=chosen.path,
            rule_id=chosen.rule_id,
            metadata={} if metadata is None else metadata,
            lineage=lineage,
        )


def build_umd_098_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_098_BUILD_ID,"revision":UMD_098_REVISION,
        "schema_version":UMD_098_SCHEMA_VERSION,"upstream_builds":("UMD-095","UMD-097"),
        "hierarchy":("asset","domain","category","subcategory","market_type"),
        "mode":"deterministic_read_only_taxonomy_classification",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})


def verify_umd_098_market_taxonomy_classification()->bool:
    if verify_umd_097_market_relationship_graph() is not True:
        return False
    m=build_umd_098_certification_manifest()
    return m["build_id"]=="UMD-098" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
