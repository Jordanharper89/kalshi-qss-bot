from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_139_observation_merge import ObservationMerge,verify_umd_139_observation_merge_resolution

UMD_140_BUILD_ID="UMD-140"
UMD_140_REVISION="UMD_140_OBSERVATION_CLUSTER_MODEL_V1"
UMD_140_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class ObservationCluster:
    cluster_id:str
    canonical_observation_ids:Tuple[str,...]
    member_observation_ids:Tuple[str,...]
    contradiction_links:Tuple[Tuple[str,str],...]
    merge_hashes:Tuple[str,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"canonical_observation_ids",tuple(self.canonical_observation_ids))
        object.__setattr__(self,"member_observation_ids",tuple(self.member_observation_ids))
        object.__setattr__(self,"contradiction_links",tuple(self.contradiction_links))
        object.__setattr__(self,"merge_hashes",tuple(self.merge_hashes))
        for name in ("canonical_observation_ids","member_observation_ids","merge_hashes"):
            value=getattr(self,name)
            if value!=tuple(sorted(set(value))):
                raise ValueError(f"{name} must be unique and sorted")
        if not self.cluster_id:
            raise ValueError("cluster_id must be non-empty")
        if self.contradiction_links!=tuple(sorted(set(self.contradiction_links))):
            raise ValueError("contradiction_links must be unique and sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_140_BUILD_ID:
            raise ValueError("lineage must belong to UMD-140")
        if not set(self.merge_hashes).issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every merge hash")

    @property
    def cluster_hash(self)->str:
        return deterministic_sha256({
            "cluster_id":self.cluster_id,
            "canonical_observation_ids":self.canonical_observation_ids,
            "member_observation_ids":self.member_observation_ids,
            "contradiction_links":self.contradiction_links,
            "merge_hashes":self.merge_hashes,
            "lineage":self.lineage,
        })

class ObservationClusterBuilder:
    __slots__=()

    def build(
        self,
        cluster_id:str,
        merges:Iterable[ObservationMerge],
        *,
        lineage:ImmutableLineage,
    )->ObservationCluster:
        values=tuple(merges)
        if any(not isinstance(m,ObservationMerge) for m in values):
            raise TypeError("merges must contain ObservationMerge")
        canonical=tuple(sorted(m.canonical_observation_id for m in values))
        members=tuple(sorted({x for m in values for x in m.member_observation_ids}))
        known=set(members)
        links=set()
        for merge in values:
            for peer in merge.contradiction_peer_ids:
                if peer in known:
                    links.add(tuple(sorted((merge.canonical_observation_id,peer))))
        hashes=tuple(sorted(m.merge_hash for m in values))
        return ObservationCluster(cluster_id,canonical,members,tuple(sorted(links)),hashes,lineage)

def build_umd_140_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_140_BUILD_ID,"revision":UMD_140_REVISION,
        "schema_version":UMD_140_SCHEMA_VERSION,"upstream_builds":("UMD-139",),
        "mode":"deterministic_read_only_observation_cluster_model",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_140_observation_cluster_model()->bool:
    if verify_umd_139_observation_merge_resolution() is not True:
        return False
    m=build_umd_140_certification_manifest()
    return m["build_id"]=="UMD-140" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
