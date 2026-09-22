from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_139_observation_merge import ObservationMerge
from .umd_140_observation_cluster import ObservationCluster,verify_umd_140_observation_cluster_model

UMD_141_BUILD_ID="UMD-141"
UMD_141_REVISION="UMD_141_OBSERVATION_STATE_REGISTRY_V1"
UMD_141_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ObservationStateRegistry:
    merges:Tuple[ObservationMerge,...]
    clusters:Tuple[ObservationCluster,...]
    canonical_index:Mapping[str,Tuple[str,...]]
    cluster_index:Mapping[str,Tuple[str,...]]
    contradiction_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"merges",tuple(self.merges))
        object.__setattr__(self,"clusters",tuple(self.clusters))
        for name in ("canonical_index","cluster_index","contradiction_index"):
            object.__setattr__(self,name,_freeze(getattr(self,name)))
        if self.merges!=tuple(sorted(self.merges,key=lambda m:(m.canonical_observation_id,m.merge_hash))):
            raise ValueError("merges must be deterministically sorted")
        if self.clusters!=tuple(sorted(self.clusters,key=lambda c:(c.cluster_id,c.cluster_hash))):
            raise ValueError("clusters must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_141_BUILD_ID:
            raise ValueError("lineage must belong to UMD-141")
        required={m.merge_hash for m in self.merges}|{c.cluster_hash for c in self.clusters}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every merge and cluster hash")

    def canonical_for(self,observation_id:str)->str|None:
        values=self.canonical_index.get(observation_id,())
        return values[0] if values else None

    def clusters_for(self,observation_id:str)->Tuple[str,...]:
        return self.cluster_index.get(observation_id,())

    def contradictions_for(self,canonical_observation_id:str)->Tuple[str,...]:
        return self.contradiction_index.get(canonical_observation_id,())

    @property
    def registry_hash(self)->str:
        return deterministic_sha256({
            "merge_hashes":tuple(m.merge_hash for m in self.merges),
            "cluster_hashes":tuple(c.cluster_hash for c in self.clusters),
            "canonical_index":self.canonical_index,
            "cluster_index":self.cluster_index,
            "contradiction_index":self.contradiction_index,
            "lineage":self.lineage,
        })

class ObservationStateRegistryBuilder:
    __slots__=()

    def build(
        self,
        merges:Iterable[ObservationMerge],
        clusters:Iterable[ObservationCluster],
        *,
        lineage_factory,
    )->ObservationStateRegistry:
        ms=tuple(merges)
        cs=tuple(clusters)
        if any(not isinstance(m,ObservationMerge) for m in ms):
            raise TypeError("merges must contain ObservationMerge")
        if any(not isinstance(c,ObservationCluster) for c in cs):
            raise TypeError("clusters must contain ObservationCluster")

        ms=tuple(sorted(ms,key=lambda m:(m.canonical_observation_id,m.merge_hash)))
        cs=tuple(sorted(cs,key=lambda c:(c.cluster_id,c.cluster_hash)))

        canonical={}
        cluster={}
        contradiction={}

        for merge in ms:
            for obs in merge.member_observation_ids:
                existing=canonical.get(obs)
                value=(merge.canonical_observation_id,)
                if existing is not None and existing!=value:
                    raise ValueError("observation belongs to more than one canonical merge")
                canonical[obs]=value
            contradiction[merge.canonical_observation_id]=merge.contradiction_peer_ids

        for c in cs:
            for obs in c.member_observation_ids:
                cluster.setdefault(obs,[]).append(c.cluster_id)

        for key,values in cluster.items():
            cluster[key]=tuple(sorted(set(values)))

        parents=tuple(m.merge_hash for m in ms)+tuple(c.cluster_hash for c in cs)
        lineage=lineage_factory(parents)
        return ObservationStateRegistry(ms,cs,canonical,cluster,contradiction,lineage)

def build_umd_141_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_141_BUILD_ID,"revision":UMD_141_REVISION,
        "schema_version":UMD_141_SCHEMA_VERSION,"upstream_builds":("UMD-139","UMD-140"),
        "mode":"deterministic_read_only_observation_state_registry",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_141_observation_state_registry()->bool:
    if verify_umd_140_observation_cluster_model() is not True:
        return False
    m=build_umd_141_certification_manifest()
    return m["build_id"]=="UMD-141" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
