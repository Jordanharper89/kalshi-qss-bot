from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_135_observation_routing_registry import ObservationRoutingRecord,verify_umd_135_observation_routing_registry

UMD_136_BUILD_ID="UMD-136"
UMD_136_REVISION="UMD_136_OBSERVATION_EQUIVALENCE_RESOLUTION_V1"
UMD_136_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def observation_signature(record:ObservationRoutingRecord)->str:
    if not isinstance(record,ObservationRoutingRecord):
        raise TypeError("record must be ObservationRoutingRecord")
    return deterministic_sha256({
        "domain":record.domain,
        "market_ids":record.market_ids,
        "family_keys":record.family_keys,
        "venue_keys":record.venue_keys,
        "unresolved_entities":record.unresolved_entities,
    })

@dataclass(frozen=True,slots=True)
class ObservationEquivalenceGroup:
    signature_hash:str
    canonical_observation_id:str
    member_observation_ids:Tuple[str,...]
    member_record_hashes:Tuple[str,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"member_observation_ids",tuple(self.member_observation_ids))
        object.__setattr__(self,"member_record_hashes",tuple(self.member_record_hashes))
        if self.member_observation_ids!=tuple(sorted(set(self.member_observation_ids))):
            raise ValueError("member observation ids must be unique and sorted")
        if not self.member_observation_ids:
            raise ValueError("equivalence group requires at least one member")
        if self.canonical_observation_id!=self.member_observation_ids[0]:
            raise ValueError("canonical observation id must be lexicographically first member")
        if len(self.member_observation_ids)!=len(self.member_record_hashes):
            raise ValueError("member ids and record hashes length mismatch")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_136_BUILD_ID:
            raise ValueError("lineage must belong to UMD-136")
        if not set(self.member_record_hashes).issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every member record hash")

    @property
    def equivalent(self)->bool:
        return len(self.member_observation_ids)>1

    @property
    def group_hash(self)->str:
        return deterministic_sha256({
            "signature_hash":self.signature_hash,
            "canonical_observation_id":self.canonical_observation_id,
            "member_observation_ids":self.member_observation_ids,
            "member_record_hashes":self.member_record_hashes,
            "lineage":self.lineage,
        })

class ObservationEquivalenceResolver:
    __slots__=()

    def resolve(self,records:Iterable[ObservationRoutingRecord],*,lineage_factory)->Tuple[ObservationEquivalenceGroup,...]:
        values=tuple(records)
        if any(not isinstance(r,ObservationRoutingRecord) for r in values):
            raise TypeError("records must contain ObservationRoutingRecord")
        if len({r.observation_id for r in values})!=len(values):
            raise ValueError("observation ids must be unique before equivalence resolution")

        buckets={}
        for record in values:
            buckets.setdefault(observation_signature(record),[]).append(record)

        groups=[]
        for signature,members in sorted(buckets.items()):
            members=tuple(sorted(members,key=lambda r:r.observation_id))
            hashes=tuple(r.record_hash for r in members)
            lineage=lineage_factory(hashes)
            groups.append(ObservationEquivalenceGroup(
                signature,
                members[0].observation_id,
                tuple(r.observation_id for r in members),
                hashes,
                lineage,
            ))
        return tuple(sorted(groups,key=lambda g:(g.signature_hash,g.canonical_observation_id)))

def build_umd_136_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_136_BUILD_ID,"revision":UMD_136_REVISION,
        "schema_version":UMD_136_SCHEMA_VERSION,"upstream_builds":("UMD-135",),
        "mode":"deterministic_read_only_observation_equivalence_resolution",
        "equivalence_semantics":"exact_structural_signature_only_no_fuzzy_reasoning",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_136_observation_equivalence_resolution()->bool:
    if verify_umd_135_observation_routing_registry() is not True:
        return False
    m=build_umd_136_certification_manifest()
    return m["build_id"]=="UMD-136" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
