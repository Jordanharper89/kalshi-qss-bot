from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_095_market_identity import CanonicalMarketIdentity
from .umd_096_duplicate_resolution import DuplicateGroup
from .umd_097_market_relationship_graph import MarketRelationshipGraph
from .umd_098_market_taxonomy import MarketTaxonomyClassification
from .umd_099_market_alias_resolution import AliasIndex
from .umd_100_market_lifecycle import MarketLifecycle
from .umd_101_outcome_schema import OutcomeSchema, verify_umd_101_outcome_schema_resolution

UMD_102_BUILD_ID="UMD-102"
UMD_102_BUILD_NAME="Canonical Market Record Assembly"
UMD_102_REVISION="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1"
UMD_102_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")


def _freeze(value:Mapping[str,Any] | None)->Mapping[str,Any]:
    if value is None: value={}
    if not isinstance(value,Mapping): raise TypeError("metadata must be a mapping")
    return MappingProxyType(dict(sorted((str(k),v) for k,v in value.items())))


@dataclass(frozen=True,slots=True)
class VenueMarketBinding:
    venue_key:str
    venue_market_id:str
    identity_hash:str
    def __post_init__(self):
        if not self.venue_key or not self.venue_market_id: raise ValueError("venue binding fields must be non-empty")
        if not isinstance(self.identity_hash,str) or len(self.identity_hash)!=64: raise ValueError("identity_hash must be SHA-256 hex")
    def to_canonical_dict(self): return {"venue_key":self.venue_key,"venue_market_id":self.venue_market_id,"identity_hash":self.identity_hash}
    @property
    def binding_hash(self): return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True,slots=True)
class CanonicalMarketRecord:
    canonical_market_id:str
    primary_identity_hash:str
    venue_bindings:Tuple[VenueMarketBinding,...]
    taxonomy_key:str
    lifecycle_hash:str
    outcome_schema_hash:str
    alias_keys:Tuple[str,...]
    relationship_hashes:Tuple[str,...]
    duplicate_group_hash:str
    metadata:Mapping[str,Any]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"venue_bindings",tuple(self.venue_bindings)); object.__setattr__(self,"alias_keys",tuple(self.alias_keys)); object.__setattr__(self,"relationship_hashes",tuple(self.relationship_hashes)); object.__setattr__(self,"metadata",_freeze(self.metadata))
        if not self.venue_bindings: raise ValueError("canonical record requires at least one venue binding")
        if self.primary_identity_hash!=min(x.identity_hash for x in self.venue_bindings): raise ValueError("primary identity must be deterministic minimum hash")
        if tuple(sorted(set(self.alias_keys)))!=self.alias_keys: raise ValueError("alias_keys must be sorted and unique")
        if tuple(sorted(set(self.relationship_hashes)))!=self.relationship_hashes: raise ValueError("relationship_hashes must be sorted and unique")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_102_BUILD_ID: raise ValueError("lineage must belong to UMD-102")

    def to_canonical_dict(self):
        return {"canonical_market_id":self.canonical_market_id,"primary_identity_hash":self.primary_identity_hash,
                "venue_binding_hashes":tuple(x.binding_hash for x in self.venue_bindings),"taxonomy_key":self.taxonomy_key,
                "lifecycle_hash":self.lifecycle_hash,"outcome_schema_hash":self.outcome_schema_hash,"alias_keys":self.alias_keys,
                "relationship_hashes":self.relationship_hashes,"duplicate_group_hash":self.duplicate_group_hash,"metadata":self.metadata,"lineage":self.lineage}
    @property
    def record_hash(self): return deterministic_sha256(self.to_canonical_dict())


class CanonicalMarketRecordAssembler:
    __slots__=()
    def assemble(self,identities:Iterable[CanonicalMarketIdentity],*,classification:MarketTaxonomyClassification,lifecycle:MarketLifecycle,
                 outcome_schema:OutcomeSchema,alias_index:AliasIndex,relationship_graph:MarketRelationshipGraph,lineage:ImmutableLineage,
                 duplicate_group:DuplicateGroup | None=None,metadata:Mapping[str,Any] | None=None)->CanonicalMarketRecord:
        values=tuple(identities)
        if not values or any(not isinstance(x,CanonicalMarketIdentity) for x in values): raise TypeError("identities must contain CanonicalMarketIdentity")
        canonical_ids={x.canonical_market_id for x in values}
        if len(canonical_ids)!=1: raise ValueError("all identities must represent the same canonical market")
        canonical_id=next(iter(canonical_ids)); ordered=tuple(sorted(values,key=lambda x:(x.identity_hash,x.venue_key,x.venue_market_id)))
        if len({x.identity_hash for x in ordered})!=len(ordered): raise ValueError("identity hashes must be unique")
        primary=ordered[0]
        if classification.canonical_market_id!=canonical_id or classification.identity_hash!=primary.identity_hash: raise ValueError("classification must belong to primary identity")
        if lifecycle.canonical_market_id!=canonical_id or lifecycle.identity_hash!=primary.identity_hash: raise ValueError("lifecycle must belong to primary identity")
        if outcome_schema.canonical_market_id!=canonical_id or outcome_schema.identity_hash!=primary.identity_hash: raise ValueError("outcome schema must belong to primary identity")
        if canonical_id not in relationship_graph.market_ids: raise ValueError("relationship graph must contain canonical market")
        venues={x.venue_key for x in ordered}
        if len(venues)>1:
            if duplicate_group is None: raise ValueError("cross-venue record requires duplicate group")
            if duplicate_group.canonical_market_id!=canonical_id or set(duplicate_group.member_identity_hashes)!={x.identity_hash for x in ordered}: raise ValueError("duplicate group does not match identities")
            if duplicate_group.primary_identity_hash!=primary.identity_hash: raise ValueError("duplicate group primary identity mismatch")
        elif duplicate_group is not None: raise ValueError("duplicate group is invalid for single-venue record")
        alias_keys=tuple(sorted({b.alias_key for b in alias_index.bindings if b.canonical_market_id==canonical_id}))
        relation_hashes=tuple(sorted({r.relationship_hash for r in relationship_graph.related_to(canonical_id)}))
        required={x.identity_hash for x in ordered}
        required.update((classification.classification_hash,lifecycle.lifecycle_hash,outcome_schema.outcome_schema_hash,alias_index.index_hash,relationship_graph.graph_hash))
        if duplicate_group is not None: required.add(duplicate_group.group_hash)
        if not required.issubset(set(lineage.parent_hashes)): raise ValueError("lineage must include all assembled artifact hashes")
        bindings=tuple(VenueMarketBinding(x.venue_key,x.venue_market_id,x.identity_hash) for x in ordered)
        return CanonicalMarketRecord(canonical_market_id=canonical_id,primary_identity_hash=primary.identity_hash,venue_bindings=bindings,
            taxonomy_key=classification.taxonomy_path.taxonomy_key,lifecycle_hash=lifecycle.lifecycle_hash,outcome_schema_hash=outcome_schema.outcome_schema_hash,
            alias_keys=alias_keys,relationship_hashes=relation_hashes,duplicate_group_hash="" if duplicate_group is None else duplicate_group.group_hash,
            metadata={} if metadata is None else metadata,lineage=lineage)


def build_umd_102_certification_manifest():
    data={"subsystem_id":"UMD","build_id":UMD_102_BUILD_ID,"revision":UMD_102_REVISION,"schema_version":UMD_102_SCHEMA_VERSION,
          "upstream_builds":("UMD-095","UMD-096","UMD-097","UMD-098","UMD-099","UMD-100","UMD-101"),
          "mode":"deterministic_read_only_canonical_market_record_assembly","prohibited_capabilities":PROHIBITED_CAPABILITIES,
          "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})


def verify_umd_102_canonical_market_record_assembly()->bool:
    if verify_umd_101_outcome_schema_resolution() is not True: return False
    m=build_umd_102_certification_manifest()
    return m["build_id"]=="UMD-102" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))
