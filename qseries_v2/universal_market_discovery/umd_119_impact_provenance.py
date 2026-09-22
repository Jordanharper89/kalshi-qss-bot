from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_115_observation_impact import DirectImpactResult
from .umd_118_impact_paths import ImpactPathSet,ImpactPath,verify_umd_118_impact_path_resolution

UMD_119_BUILD_ID="UMD-119"
UMD_119_REVISION="UMD_119_IMPACT_PROVENANCE_BUNDLE_V1"
UMD_119_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class MarketImpactProvenance:
    canonical_market_id:str
    direct:bool
    dependency_matches:Tuple[Tuple[str,str],...]
    market_path:Tuple[str,...]
    constraint_path:Tuple[str,...]

    def __post_init__(self):
        object.__setattr__(self,"dependency_matches",tuple(sorted(set(self.dependency_matches))))
        object.__setattr__(self,"market_path",tuple(self.market_path))
        object.__setattr__(self,"constraint_path",tuple(self.constraint_path))

    @property
    def provenance_hash(self)->str:
        return deterministic_sha256({
            "canonical_market_id":self.canonical_market_id,
            "direct":self.direct,
            "dependency_matches":self.dependency_matches,
            "market_path":self.market_path,
            "constraint_path":self.constraint_path,
        })

@dataclass(frozen=True,slots=True)
class ImpactProvenanceBundle:
    observation_hash:str
    entries:Tuple[MarketImpactProvenance,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"entries",tuple(self.entries))
        if tuple(sorted(self.entries,key=lambda e:e.canonical_market_id))!=self.entries:
            raise ValueError("entries must be sorted by canonical_market_id")
        if len({e.canonical_market_id for e in self.entries})!=len(self.entries):
            raise ValueError("duplicate canonical market provenance entry")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_119_BUILD_ID:
            raise ValueError("lineage must belong to UMD-119")

    def for_market(self,canonical_market_id:str)->MarketImpactProvenance|None:
        for entry in self.entries:
            if entry.canonical_market_id==canonical_market_id:
                return entry
        return None

    @property
    def bundle_hash(self)->str:
        return deterministic_sha256({
            "observation_hash":self.observation_hash,
            "provenance_hashes":tuple(e.provenance_hash for e in self.entries),
            "lineage":self.lineage,
        })

class ImpactProvenanceBuilder:
    __slots__=()

    def build(
        self,
        direct:DirectImpactResult,
        paths:ImpactPathSet,
        *,
        lineage:ImmutableLineage,
    )->ImpactProvenanceBundle:
        if not isinstance(direct,DirectImpactResult):
            raise TypeError("direct must be DirectImpactResult")
        if not isinstance(paths,ImpactPathSet):
            raise TypeError("paths must be ImpactPathSet")
        if direct.observation_hash!=paths.observation_hash:
            raise ValueError("observation hashes do not match")

        direct_matches={}
        for kind,key,market_ids in direct.matched_dependencies:
            for market_id in market_ids:
                direct_matches.setdefault(market_id,[]).append((kind,key))

        entries=[]
        for path in paths.paths:
            matches=tuple(sorted(set(direct_matches.get(path.target_market_id,())))) if path.direct else ()
            entries.append(MarketImpactProvenance(
                path.target_market_id,
                path.direct,
                matches,
                path.market_path,
                path.constraint_path,
            ))
        entries.sort(key=lambda e:e.canonical_market_id)
        return ImpactProvenanceBundle(direct.observation_hash,tuple(entries),lineage)

def build_umd_119_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_119_BUILD_ID,"revision":UMD_119_REVISION,
        "schema_version":UMD_119_SCHEMA_VERSION,"upstream_builds":("UMD-115","UMD-118"),
        "mode":"deterministic_read_only_impact_provenance",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_119_impact_provenance_bundle()->bool:
    if verify_umd_118_impact_path_resolution() is not True:
        return False
    m=build_umd_119_certification_manifest()
    return m["build_id"]=="UMD-119" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
