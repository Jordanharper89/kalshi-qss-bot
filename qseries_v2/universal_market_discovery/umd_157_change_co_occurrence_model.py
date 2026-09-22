from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from types import MappingProxyType
from typing import Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_156_change_market_context_registry import ChangeMarketContextRegistry,verify_umd_156_change_market_context_registry

UMD_157_BUILD_ID="UMD-157"
UMD_157_REVISION="UMD_157_CHANGE_CO_OCCURRENCE_MODEL_V1"
UMD_157_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

RELATION_ORDER=("impacted","boundary","family-neighbor","topology-neighbor")

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ChangeCoOccurrence:
    canonical_market_id:str
    change_hashes:Tuple[str,...]
    change_pairs:Tuple[Tuple[str,str],...]
    relation_types:Tuple[str,...]

    def __post_init__(self):
        object.__setattr__(self,"change_hashes",tuple(self.change_hashes))
        object.__setattr__(self,"change_pairs",tuple(self.change_pairs))
        object.__setattr__(self,"relation_types",tuple(self.relation_types))
        if not self.canonical_market_id:
            raise ValueError("canonical_market_id must be non-empty")
        if self.change_hashes!=tuple(sorted(set(self.change_hashes))):
            raise ValueError("change_hashes must be unique and sorted")
        if len(self.change_hashes)<2:
            raise ValueError("co-occurrence requires at least two distinct changes")
        expected_pairs=tuple(combinations(self.change_hashes,2))
        if self.change_pairs!=expected_pairs:
            raise ValueError("change_pairs must equal deterministic pair combinations")
        expected_relations=tuple(r for r in RELATION_ORDER if r in set(self.relation_types))
        if self.relation_types!=expected_relations:
            raise ValueError("relation_types must be unique and canonically ordered")

    @property
    def occurrence_hash(self)->str:
        return deterministic_sha256({
            "canonical_market_id":self.canonical_market_id,
            "change_hashes":self.change_hashes,
            "change_pairs":self.change_pairs,
            "relation_types":self.relation_types,
        })

@dataclass(frozen=True,slots=True)
class ChangeCoOccurrenceModel:
    occurrences:Tuple[ChangeCoOccurrence,...]
    market_index:Mapping[str,Tuple[str,...]]
    change_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"occurrences",tuple(self.occurrences))
        object.__setattr__(self,"market_index",_freeze(self.market_index))
        object.__setattr__(self,"change_index",_freeze(self.change_index))
        if self.occurrences!=tuple(sorted(
            self.occurrences,key=lambda o:(o.canonical_market_id,o.occurrence_hash)
        )):
            raise ValueError("occurrences must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_157_BUILD_ID:
            raise ValueError("lineage must belong to UMD-157")
        required={o.occurrence_hash for o in self.occurrences}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every occurrence hash")

    def changes_for_market(self,market_id:str)->Tuple[str,...]:
        return self.market_index.get(market_id,())

    def markets_for_change(self,change_hash:str)->Tuple[str,...]:
        return self.change_index.get(change_hash,())

    @property
    def model_hash(self)->str:
        return deterministic_sha256({
            "occurrence_hashes":tuple(o.occurrence_hash for o in self.occurrences),
            "market_index":self.market_index,
            "change_index":self.change_index,
            "lineage":self.lineage,
        })

class ChangeCoOccurrenceBuilder:
    __slots__=()

    def build(
        self,
        context_registry:ChangeMarketContextRegistry,
        *,
        lineage_factory,
    )->ChangeCoOccurrenceModel:
        if not isinstance(context_registry,ChangeMarketContextRegistry):
            raise TypeError("context_registry must be ChangeMarketContextRegistry")

        occurrences=[]
        market_index={}
        change_index={}

        for market_id,changes in sorted(context_registry.market_index.items()):
            change_hashes=tuple(sorted(set(changes)))
            if len(change_hashes)<2:
                continue

            relations=[]
            if market_id in context_registry.impacted_index:
                relations.append("impacted")
            if market_id in context_registry.boundary_index:
                relations.append("boundary")
            if market_id in context_registry.family_neighbor_index:
                relations.append("family-neighbor")
            if market_id in context_registry.topology_neighbor_index:
                relations.append("topology-neighbor")

            occurrence=ChangeCoOccurrence(
                market_id,
                change_hashes,
                tuple(combinations(change_hashes,2)),
                tuple(relations),
            )
            occurrences.append(occurrence)
            market_index[market_id]=change_hashes
            for change_hash in change_hashes:
                change_index.setdefault(change_hash,[]).append(market_id)

        occurrences.sort(key=lambda o:(o.canonical_market_id,o.occurrence_hash))
        for key,values in change_index.items():
            change_index[key]=tuple(sorted(set(values)))

        # The model's direct parents are the immutable co-occurrence artifacts.
        lineage=lineage_factory(tuple(o.occurrence_hash for o in occurrences))
        return ChangeCoOccurrenceModel(
            tuple(occurrences),market_index,change_index,lineage
        )

def build_umd_157_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_157_BUILD_ID,"revision":UMD_157_REVISION,
        "schema_version":UMD_157_SCHEMA_VERSION,"upstream_builds":("UMD-156",),
        "mode":"deterministic_read_only_change_co_occurrence_model",
        "semantics":"shared_structural_context_only_no_importance_or_probability",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_157_change_co_occurrence_model()->bool:
    if verify_umd_156_change_market_context_registry() is not True:
        return False
    m=build_umd_157_certification_manifest()
    return m["build_id"]=="UMD-157" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
