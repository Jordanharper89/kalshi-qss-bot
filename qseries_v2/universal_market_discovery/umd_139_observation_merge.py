from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_136_observation_equivalence import ObservationEquivalenceGroup
from .umd_138_observation_relationship_registry import ObservationRelationshipRegistry,verify_umd_138_observation_relationship_registry

UMD_139_BUILD_ID="UMD-139"
UMD_139_REVISION="UMD_139_OBSERVATION_MERGE_RESOLUTION_V1"
UMD_139_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class ObservationMerge:
    canonical_observation_id:str
    member_observation_ids:Tuple[str,...]
    equivalent_member_ids:Tuple[str,...]
    contradiction_peer_ids:Tuple[str,...]
    source_group_hash:str
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"member_observation_ids",tuple(self.member_observation_ids))
        object.__setattr__(self,"equivalent_member_ids",tuple(self.equivalent_member_ids))
        object.__setattr__(self,"contradiction_peer_ids",tuple(self.contradiction_peer_ids))
        for name in ("member_observation_ids","equivalent_member_ids","contradiction_peer_ids"):
            value=getattr(self,name)
            if value!=tuple(sorted(set(value))):
                raise ValueError(f"{name} must be unique and sorted")
        if not self.member_observation_ids:
            raise ValueError("merge requires at least one observation")
        if self.canonical_observation_id!=self.member_observation_ids[0]:
            raise ValueError("canonical observation must be first sorted member")
        if set(self.equivalent_member_ids)!=(set(self.member_observation_ids)-{self.canonical_observation_id}):
            raise ValueError("equivalent_member_ids must be all non-canonical members")
        if set(self.contradiction_peer_ids)&set(self.member_observation_ids):
            raise ValueError("contradiction peers cannot be members of same merge")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_139_BUILD_ID:
            raise ValueError("lineage must belong to UMD-139")
        if self.source_group_hash not in self.lineage.parent_hashes:
            raise ValueError("lineage must include source equivalence group hash")

    @property
    def merge_hash(self)->str:
        return deterministic_sha256({
            "canonical_observation_id":self.canonical_observation_id,
            "member_observation_ids":self.member_observation_ids,
            "equivalent_member_ids":self.equivalent_member_ids,
            "contradiction_peer_ids":self.contradiction_peer_ids,
            "source_group_hash":self.source_group_hash,
            "lineage":self.lineage,
        })

class ObservationMergeResolver:
    __slots__=("relationships",)

    def __init__(self,relationships:ObservationRelationshipRegistry):
        if not isinstance(relationships,ObservationRelationshipRegistry):
            raise TypeError("relationships must be ObservationRelationshipRegistry")
        self.relationships=relationships

    def resolve(
        self,
        groups:Iterable[ObservationEquivalenceGroup],
        *,
        lineage_factory,
    )->Tuple[ObservationMerge,...]:
        values=tuple(groups)
        if any(not isinstance(g,ObservationEquivalenceGroup) for g in values):
            raise TypeError("groups must contain ObservationEquivalenceGroup")

        merges=[]
        for group in sorted(values,key=lambda g:(g.signature_hash,g.canonical_observation_id)):
            peers=set()
            for member in group.member_observation_ids:
                peers.update(self.relationships.contradictions_of(member))
            peers.difference_update(group.member_observation_ids)

            lineage=lineage_factory((group.group_hash,))
            merges.append(ObservationMerge(
                group.canonical_observation_id,
                group.member_observation_ids,
                tuple(x for x in group.member_observation_ids if x!=group.canonical_observation_id),
                tuple(sorted(peers)),
                group.group_hash,
                lineage,
            ))
        return tuple(sorted(merges,key=lambda m:(m.canonical_observation_id,m.merge_hash)))

def build_umd_139_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_139_BUILD_ID,"revision":UMD_139_REVISION,
        "schema_version":UMD_139_SCHEMA_VERSION,"upstream_builds":("UMD-136","UMD-138"),
        "mode":"deterministic_read_only_observation_merge_resolution",
        "merge_semantics":"equivalence_collapse_with_contradiction_preservation",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_139_observation_merge_resolution()->bool:
    if verify_umd_138_observation_relationship_registry() is not True:
        return False
    m=build_umd_139_certification_manifest()
    return m["build_id"]=="UMD-139" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
