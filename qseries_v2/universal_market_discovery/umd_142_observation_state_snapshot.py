from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_141_observation_state_registry import ObservationStateRegistry, verify_umd_141_observation_state_registry

UMD_142_BUILD_ID="UMD-142"
UMD_142_REVISION="UMD_142_OBSERVATION_STATE_SNAPSHOT_V1"
UMD_142_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _utc(value:datetime)->datetime:
    if not isinstance(value,datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")
    return value.astimezone(timezone.utc)

@dataclass(frozen=True,slots=True)
class ObservationStateSnapshot:
    as_of:datetime
    registry_hash:str
    canonical_observation_ids:Tuple[str,...]
    cluster_ids:Tuple[str,...]
    contradiction_pairs:Tuple[Tuple[str,str],...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"as_of",_utc(self.as_of))
        object.__setattr__(self,"canonical_observation_ids",tuple(self.canonical_observation_ids))
        object.__setattr__(self,"cluster_ids",tuple(self.cluster_ids))
        object.__setattr__(self,"contradiction_pairs",tuple(self.contradiction_pairs))
        for name in ("canonical_observation_ids","cluster_ids"):
            value=getattr(self,name)
            if value!=tuple(sorted(set(value))):
                raise ValueError(f"{name} must be unique and sorted")
        if self.contradiction_pairs!=tuple(sorted(set(self.contradiction_pairs))):
            raise ValueError("contradiction_pairs must be unique and sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_142_BUILD_ID:
            raise ValueError("lineage must belong to UMD-142")
        if self.registry_hash not in self.lineage.parent_hashes:
            raise ValueError("lineage must include state registry hash")

    @property
    def snapshot_hash(self)->str:
        return deterministic_sha256({
            "as_of":self.as_of,
            "registry_hash":self.registry_hash,
            "canonical_observation_ids":self.canonical_observation_ids,
            "cluster_ids":self.cluster_ids,
            "contradiction_pairs":self.contradiction_pairs,
            "lineage":self.lineage,
        })

class ObservationStateSnapshotBuilder:
    __slots__=()

    def build(
        self,
        registry:ObservationStateRegistry,
        *,
        as_of:datetime,
        lineage:ImmutableLineage,
    )->ObservationStateSnapshot:
        if not isinstance(registry,ObservationStateRegistry):
            raise TypeError("registry must be ObservationStateRegistry")

        canonical=tuple(sorted({m.canonical_observation_id for m in registry.merges}))
        clusters=tuple(sorted({c.cluster_id for c in registry.clusters}))
        pairs=set()

        known_canonical=set(canonical)
        for merge in registry.merges:
            for peer in merge.contradiction_peer_ids:
                left=merge.canonical_observation_id
                right=registry.canonical_for(peer) or peer
                if left==right:
                    continue
                pair=tuple(sorted((left,right)))
                pairs.add(pair)

        return ObservationStateSnapshot(
            as_of,
            registry.registry_hash,
            canonical,
            clusters,
            tuple(sorted(pairs)),
            lineage,
        )

def build_umd_142_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_142_BUILD_ID,"revision":UMD_142_REVISION,
        "schema_version":UMD_142_SCHEMA_VERSION,"upstream_builds":("UMD-141",),
        "mode":"deterministic_read_only_observation_state_snapshot",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_142_observation_state_snapshot()->bool:
    if verify_umd_141_observation_state_registry() is not True:
        return False
    m=build_umd_142_certification_manifest()
    return m["build_id"]=="UMD-142" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
