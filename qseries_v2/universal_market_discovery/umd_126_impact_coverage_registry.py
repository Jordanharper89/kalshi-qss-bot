from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_125_impact_coverage_matrix import ImpactCoverageMatrix, verify_umd_125_impact_coverage_matrix

UMD_126_BUILD_ID="UMD-126"
UMD_126_REVISION="UMD_126_IMPACT_COVERAGE_REGISTRY_V1"
UMD_126_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

def _freeze_index(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ImpactCoverageRegistry:
    matrices:Tuple[ImpactCoverageMatrix,...]
    family_index:Mapping[str,Tuple[str,...]]
    venue_index:Mapping[str,Tuple[str,...]]
    cross_venue_index:Mapping[str,Tuple[str,...]]
    market_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"matrices",tuple(self.matrices))
        for name in ("family_index","venue_index","cross_venue_index","market_index"):
            object.__setattr__(self,name,_freeze_index(getattr(self,name)))
        if self.matrices!=tuple(sorted(self.matrices,key=lambda m:(m.observation_hash,m.matrix_hash))):
            raise ValueError("matrices must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_126_BUILD_ID:
            raise ValueError("lineage must belong to UMD-126")
        required={m.matrix_hash for m in self.matrices}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every matrix hash")

    def observations_for_family(self,family_key:str)->Tuple[str,...]:
        return self.family_index.get(family_key,())

    def observations_for_venue(self,venue_key:str)->Tuple[str,...]:
        return self.venue_index.get(venue_key,())

    def observations_for_cross_venue_market(self,canonical_market_id:str)->Tuple[str,...]:
        return self.cross_venue_index.get(canonical_market_id,())

    def observations_for_market(self,canonical_market_id:str)->Tuple[str,...]:
        return self.market_index.get(canonical_market_id,())

    def observations_for_family_and_venue(self,family_key:str,venue_key:str)->Tuple[str,...]:
        return tuple(sorted(
            set(self.observations_for_family(family_key)) &
            set(self.observations_for_venue(venue_key))
        ))

    @property
    def registry_hash(self)->str:
        return deterministic_sha256({
            "matrix_hashes":tuple(m.matrix_hash for m in self.matrices),
            "family_index":self.family_index,
            "venue_index":self.venue_index,
            "cross_venue_index":self.cross_venue_index,
            "market_index":self.market_index,
            "lineage":self.lineage,
        })

class ImpactCoverageRegistryBuilder:
    __slots__=()

    def build(
        self,
        matrices:Iterable[ImpactCoverageMatrix],
        *,
        lineage_factory,
    )->ImpactCoverageRegistry:
        values=tuple(matrices)
        if any(not isinstance(m,ImpactCoverageMatrix) for m in values):
            raise TypeError("matrices must contain ImpactCoverageMatrix")
        values=tuple(sorted(values,key=lambda m:(m.observation_hash,m.matrix_hash)))

        family={}
        venue={}
        cross={}
        market={}

        for matrix in values:
            obs=matrix.observation_hash
            for family_key in matrix.family_to_markets:
                family.setdefault(family_key,[]).append(obs)
            for venue_key in matrix.venue_to_markets:
                venue.setdefault(venue_key,[]).append(obs)
            for market_id in matrix.cross_venue_market_ids:
                cross.setdefault(market_id,[]).append(obs)
            all_markets=set(matrix.direct_market_ids)|set(matrix.propagated_market_ids)
            for market_id in all_markets:
                market.setdefault(market_id,[]).append(obs)

        for index in (family,venue,cross,market):
            for key,obs in index.items():
                index[key]=tuple(sorted(set(obs)))

        lineage=lineage_factory(tuple(m.matrix_hash for m in values))
        return ImpactCoverageRegistry(values,family,venue,cross,market,lineage)

def build_umd_126_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_126_BUILD_ID,"revision":UMD_126_REVISION,
        "schema_version":UMD_126_SCHEMA_VERSION,"upstream_builds":("UMD-125",),
        "mode":"deterministic_read_only_impact_coverage_registry",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_126_impact_coverage_registry()->bool:
    if verify_umd_125_impact_coverage_matrix() is not True:
        return False
    m=build_umd_126_certification_manifest()
    return m["build_id"]=="UMD-126" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
