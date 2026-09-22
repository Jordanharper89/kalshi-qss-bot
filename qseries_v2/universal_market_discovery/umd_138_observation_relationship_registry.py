from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_136_observation_equivalence import ObservationEquivalenceGroup
from .umd_137_observation_contradiction import ObservationContradictionSet,verify_umd_137_observation_contradiction_model

UMD_138_BUILD_ID="UMD-138"
UMD_138_REVISION="UMD_138_OBSERVATION_RELATIONSHIP_REGISTRY_V1"
UMD_138_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ObservationRelationshipRegistry:
    equivalence_groups:Tuple[ObservationEquivalenceGroup,...]
    contradiction_sets:Tuple[ObservationContradictionSet,...]
    equivalent_index:Mapping[str,Tuple[str,...]]
    contradiction_index:Mapping[str,Tuple[str,...]]
    contradiction_type_index:Mapping[str,Tuple[str,...]]
    canonical_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"equivalence_groups",tuple(self.equivalence_groups))
        object.__setattr__(self,"contradiction_sets",tuple(self.contradiction_sets))
        for name in ("equivalent_index","contradiction_index","contradiction_type_index","canonical_index"):
            object.__setattr__(self,name,_freeze(getattr(self,name)))
        if self.equivalence_groups!=tuple(sorted(
            self.equivalence_groups,key=lambda g:(g.signature_hash,g.canonical_observation_id)
        )):
            raise ValueError("equivalence groups must be deterministically sorted")
        if self.contradiction_sets!=tuple(sorted(
            self.contradiction_sets,key=lambda s:s.contradiction_set_hash
        )):
            raise ValueError("contradiction sets must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_138_BUILD_ID:
            raise ValueError("lineage must belong to UMD-138")
        required={g.group_hash for g in self.equivalence_groups}|{s.contradiction_set_hash for s in self.contradiction_sets}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every relationship artifact hash")

    def equivalents_of(self,observation_id:str)->Tuple[str,...]:
        return self.equivalent_index.get(observation_id,())

    def contradictions_of(self,observation_id:str)->Tuple[str,...]:
        return self.contradiction_index.get(observation_id,())

    def observations_for_contradiction_type(self,kind:str)->Tuple[str,...]:
        return self.contradiction_type_index.get(kind,())

    def canonical_for(self,observation_id:str)->str|None:
        values=self.canonical_index.get(observation_id,())
        return values[0] if values else None

    @property
    def registry_hash(self)->str:
        return deterministic_sha256({
            "equivalence_group_hashes":tuple(g.group_hash for g in self.equivalence_groups),
            "contradiction_set_hashes":tuple(s.contradiction_set_hash for s in self.contradiction_sets),
            "equivalent_index":self.equivalent_index,
            "contradiction_index":self.contradiction_index,
            "contradiction_type_index":self.contradiction_type_index,
            "canonical_index":self.canonical_index,
            "lineage":self.lineage,
        })

class ObservationRelationshipRegistryBuilder:
    __slots__=()

    def build(
        self,
        equivalence_groups:Iterable[ObservationEquivalenceGroup],
        contradiction_sets:Iterable[ObservationContradictionSet],
        *,
        lineage_factory,
    )->ObservationRelationshipRegistry:
        groups=tuple(equivalence_groups)
        sets=tuple(contradiction_sets)

        if any(not isinstance(g,ObservationEquivalenceGroup) for g in groups):
            raise TypeError("equivalence_groups must contain ObservationEquivalenceGroup")
        if any(not isinstance(s,ObservationContradictionSet) for s in sets):
            raise TypeError("contradiction_sets must contain ObservationContradictionSet")

        groups=tuple(sorted(groups,key=lambda g:(g.signature_hash,g.canonical_observation_id)))
        sets=tuple(sorted(sets,key=lambda s:s.contradiction_set_hash))

        equivalent={}
        contradiction={}
        contradiction_type={}
        canonical={}

        for group in groups:
            members=group.member_observation_ids
            for obs in members:
                equivalent[obs]=tuple(x for x in members if x!=obs)
                canonical[obs]=(group.canonical_observation_id,)

        for contradiction_set in sets:
            for edge in contradiction_set.contradictions:
                contradiction.setdefault(edge.source_observation_id,[]).append(edge.target_observation_id)
                contradiction.setdefault(edge.target_observation_id,[]).append(edge.source_observation_id)
                contradiction_type.setdefault(edge.contradiction_type,[]).extend(
                    (edge.source_observation_id,edge.target_observation_id)
                )

        for index in (contradiction,contradiction_type):
            for key,values in index.items():
                index[key]=tuple(sorted(set(values)))

        parents=tuple(g.group_hash for g in groups)+tuple(s.contradiction_set_hash for s in sets)
        lineage=lineage_factory(parents)
        return ObservationRelationshipRegistry(
            groups,sets,equivalent,contradiction,contradiction_type,canonical,lineage
        )

def build_umd_138_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_138_BUILD_ID,"revision":UMD_138_REVISION,
        "schema_version":UMD_138_SCHEMA_VERSION,"upstream_builds":("UMD-136","UMD-137"),
        "mode":"deterministic_read_only_observation_relationship_registry",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_138_observation_relationship_registry()->bool:
    if verify_umd_137_observation_contradiction_model() is not True:
        return False
    m=build_umd_138_certification_manifest()
    return m["build_id"]=="UMD-138" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
