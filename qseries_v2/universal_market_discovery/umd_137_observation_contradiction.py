from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_136_observation_equivalence import ObservationEquivalenceGroup,verify_umd_136_observation_equivalence_resolution

UMD_137_BUILD_ID="UMD-137"
UMD_137_REVISION="UMD_137_OBSERVATION_CONTRADICTION_MODEL_V1"
UMD_137_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")
CONTRADICTION_TYPES=("negates","supersedes","mutually-exclusive","temporal-conflict")
SYMMETRIC_CONTRADICTIONS=("mutually-exclusive",)

@dataclass(frozen=True,slots=True)
class ObservationContradiction:
    source_observation_id:str
    target_observation_id:str
    contradiction_type:str
    basis_key:str

    def __post_init__(self):
        if not self.source_observation_id or not self.target_observation_id:
            raise ValueError("contradiction endpoints must be non-empty")
        if self.source_observation_id==self.target_observation_id:
            raise ValueError("contradiction endpoints must differ")
        if self.contradiction_type not in CONTRADICTION_TYPES:
            raise ValueError("unsupported contradiction type")
        if not isinstance(self.basis_key,str) or not self.basis_key.strip():
            raise ValueError("basis_key must be non-empty")

    @property
    def contradiction_hash(self)->str:
        return deterministic_sha256({
            "source_observation_id":self.source_observation_id,
            "target_observation_id":self.target_observation_id,
            "contradiction_type":self.contradiction_type,
            "basis_key":self.basis_key,
        })

@dataclass(frozen=True,slots=True)
class ObservationContradictionSet:
    observation_ids:Tuple[str,...]
    contradictions:Tuple[ObservationContradiction,...]
    equivalence_group_hashes:Tuple[str,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"observation_ids",tuple(self.observation_ids))
        object.__setattr__(self,"contradictions",tuple(self.contradictions))
        object.__setattr__(self,"equivalence_group_hashes",tuple(self.equivalence_group_hashes))
        if self.observation_ids!=tuple(sorted(set(self.observation_ids))):
            raise ValueError("observation_ids must be unique and sorted")
        expected=tuple(sorted(
            self.contradictions,
            key=lambda c:(c.source_observation_id,c.target_observation_id,c.contradiction_type,c.basis_key)
        ))
        if self.contradictions!=expected:
            raise ValueError("contradictions must be deterministically sorted")
        known=set(self.observation_ids)
        for c in self.contradictions:
            if c.source_observation_id not in known or c.target_observation_id not in known:
                raise ValueError("contradiction references unknown observation")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_137_BUILD_ID:
            raise ValueError("lineage must belong to UMD-137")
        if not set(self.equivalence_group_hashes).issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include equivalence group hashes")

    def contradictions_for(self,observation_id:str)->Tuple[ObservationContradiction,...]:
        return tuple(c for c in self.contradictions if observation_id in (c.source_observation_id,c.target_observation_id))

    @property
    def contradiction_set_hash(self)->str:
        return deterministic_sha256({
            "observation_ids":self.observation_ids,
            "contradiction_hashes":tuple(c.contradiction_hash for c in self.contradictions),
            "equivalence_group_hashes":self.equivalence_group_hashes,
            "lineage":self.lineage,
        })

class ObservationContradictionBuilder:
    __slots__=()

    def build(
        self,
        equivalence_groups:Iterable[ObservationEquivalenceGroup],
        specs:Iterable[tuple[str,str,str,str]],
        *,
        lineage:ImmutableLineage,
    )->ObservationContradictionSet:
        groups=tuple(equivalence_groups)
        if any(not isinstance(g,ObservationEquivalenceGroup) for g in groups):
            raise TypeError("equivalence_groups must contain ObservationEquivalenceGroup")

        observation_ids=tuple(sorted({
            obs for group in groups for obs in group.member_observation_ids
        }))
        known=set(observation_ids)
        contradictions=[]
        seen=set()

        for source,target,kind,basis in specs:
            if source not in known or target not in known:
                raise ValueError("contradiction references unknown observation")
            if kind in SYMMETRIC_CONTRADICTIONS and target<source:
                source,target=target,source
            key=(source,target,kind,basis)
            if key in seen:
                continue
            seen.add(key)
            contradictions.append(ObservationContradiction(source,target,kind,basis))

        contradictions.sort(key=lambda c:(c.source_observation_id,c.target_observation_id,c.contradiction_type,c.basis_key))
        return ObservationContradictionSet(
            observation_ids,
            tuple(contradictions),
            tuple(sorted(g.group_hash for g in groups)),
            lineage,
        )

def build_umd_137_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_137_BUILD_ID,"revision":UMD_137_REVISION,
        "schema_version":UMD_137_SCHEMA_VERSION,"upstream_builds":("UMD-136",),
        "mode":"deterministic_read_only_explicit_observation_contradiction_model",
        "contradiction_types":CONTRADICTION_TYPES,
        "contradiction_semantics":"explicit_structural_relationships_only_no_inference",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_137_observation_contradiction_model()->bool:
    if verify_umd_136_observation_equivalence_resolution() is not True:
        return False
    m=build_umd_137_certification_manifest()
    return m["build_id"]=="UMD-137" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
