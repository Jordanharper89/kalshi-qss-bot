from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_095_market_identity import CanonicalMarketIdentity
from .umd_096_duplicate_resolution import verify_umd_096_cross_venue_duplicate_resolution

UMD_097_BUILD_ID="UMD-097"
UMD_097_BUILD_NAME="Market Relationship Graph"
UMD_097_REVISION="UMD_097_MARKET_RELATIONSHIP_GRAPH_V1"
UMD_097_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")
RELATION_TYPES=("parent","child","complementary","opposing","conditional","successor","predecessor","related")
DIRECTED_RELATION_TYPES=("parent","child","conditional","successor","predecessor")


def _freeze(value: Mapping[str,Any] | None) -> Mapping[str,Any]:
    if value is None:
        value={}
    if not isinstance(value,Mapping):
        raise TypeError("metadata must be a mapping")
    return MappingProxyType(dict(sorted((str(k),v) for k,v in value.items())))


@dataclass(frozen=True,slots=True)
class RelationshipSpec:
    source_market_id:str
    target_market_id:str
    relation_type:str
    evidence_refs:Tuple[str,...]=()
    metadata:Mapping[str,Any] | None=None

    def __post_init__(self):
        if not isinstance(self.source_market_id,str) or not self.source_market_id:
            raise ValueError("source_market_id must be non-empty")
        if not isinstance(self.target_market_id,str) or not self.target_market_id:
            raise ValueError("target_market_id must be non-empty")
        if self.source_market_id==self.target_market_id:
            raise ValueError("relationship endpoints must differ")
        if self.relation_type not in RELATION_TYPES:
            raise ValueError("unsupported relation_type")
        refs=tuple(self.evidence_refs)
        if any(not isinstance(x,str) or not x for x in refs):
            raise ValueError("evidence_refs must contain non-empty strings")
        if len(set(refs))!=len(refs):
            raise ValueError("evidence_refs must be unique")
        object.__setattr__(self,"evidence_refs",refs)
        object.__setattr__(self,"metadata",_freeze(self.metadata))


@dataclass(frozen=True,slots=True)
class MarketRelationship:
    source_market_id:str
    target_market_id:str
    relation_type:str
    directed:bool
    evidence_refs:Tuple[str,...]
    metadata:Mapping[str,Any]
    lineage:ImmutableLineage

    def __post_init__(self):
        if self.relation_type not in RELATION_TYPES:
            raise ValueError("unsupported relation_type")
        if self.directed != (self.relation_type in DIRECTED_RELATION_TYPES):
            raise ValueError("directed flag does not match relation type")
        object.__setattr__(self,"evidence_refs",tuple(self.evidence_refs))
        object.__setattr__(self,"metadata",_freeze(self.metadata))
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_097_BUILD_ID:
            raise ValueError("lineage must belong to UMD-097")

    def to_canonical_dict(self):
        return {
            "source_market_id":self.source_market_id,
            "target_market_id":self.target_market_id,
            "relation_type":self.relation_type,
            "directed":self.directed,
            "evidence_refs":self.evidence_refs,
            "metadata":self.metadata,
            "lineage":self.lineage,
        }

    @property
    def relationship_hash(self):
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True,slots=True)
class MarketRelationshipGraph:
    market_ids:Tuple[str,...]
    relationships:Tuple[MarketRelationship,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"market_ids",tuple(self.market_ids))
        object.__setattr__(self,"relationships",tuple(self.relationships))
        if len(set(self.market_ids))!=len(self.market_ids):
            raise ValueError("market_ids must be unique")
        known=set(self.market_ids)
        for edge in self.relationships:
            if edge.source_market_id not in known or edge.target_market_id not in known:
                raise ValueError("relationship endpoint missing from graph")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_097_BUILD_ID:
            raise ValueError("graph lineage must belong to UMD-097")

    def to_canonical_dict(self):
        return {
            "market_ids":self.market_ids,
            "relationship_hashes":tuple(x.relationship_hash for x in self.relationships),
            "lineage":self.lineage,
        }

    @property
    def graph_hash(self):
        return deterministic_sha256(self.to_canonical_dict())

    def related_to(self, canonical_market_id:str) -> Tuple[MarketRelationship,...]:
        return tuple(
            edge for edge in self.relationships
            if edge.source_market_id==canonical_market_id or edge.target_market_id==canonical_market_id
        )


class MarketRelationshipGraphBuilder:
    __slots__=()

    def build(
        self,
        identities:Iterable[CanonicalMarketIdentity],
        specs:Iterable[RelationshipSpec],
        *,
        lineage:ImmutableLineage,
    ) -> MarketRelationshipGraph:
        ids=tuple(identities)
        if any(not isinstance(x,CanonicalMarketIdentity) for x in ids):
            raise TypeError("identities must contain CanonicalMarketIdentity")
        market_ids=tuple(sorted({x.canonical_market_id for x in ids}))
        required={x.identity_hash for x in ids}
        if not required.issubset(set(lineage.parent_hashes)):
            raise ValueError("lineage must include every identity hash")
        known=set(market_ids)
        edges=[]
        seen=set()
        for spec in specs:
            if not isinstance(spec,RelationshipSpec):
                raise TypeError("specs must contain RelationshipSpec")
            if spec.source_market_id not in known or spec.target_market_id not in known:
                raise ValueError("relationship spec references unknown market")
            source,target=spec.source_market_id,spec.target_market_id
            directed=spec.relation_type in DIRECTED_RELATION_TYPES
            if not directed and target < source:
                source,target=target,source
            key=(source,target,spec.relation_type)
            if key in seen:
                raise ValueError("duplicate relationship specification")
            seen.add(key)
            edges.append(MarketRelationship(
                source_market_id=source,
                target_market_id=target,
                relation_type=spec.relation_type,
                directed=directed,
                evidence_refs=tuple(sorted(spec.evidence_refs)),
                metadata=spec.metadata,
                lineage=lineage,
            ))
        edges.sort(key=lambda x:(x.source_market_id,x.target_market_id,x.relation_type,x.relationship_hash))
        return MarketRelationshipGraph(market_ids=market_ids,relationships=tuple(edges),lineage=lineage)


def build_umd_097_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_097_BUILD_ID,"revision":UMD_097_REVISION,
        "schema_version":UMD_097_SCHEMA_VERSION,"upstream_builds":("UMD-095","UMD-096"),
        "mode":"deterministic_read_only_relationship_graph",
        "relation_types":RELATION_TYPES,
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})


def verify_umd_097_market_relationship_graph()->bool:
    if verify_umd_096_cross_venue_duplicate_resolution() is not True:
        return False
    m=build_umd_097_certification_manifest()
    return m["build_id"]=="UMD-097" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
