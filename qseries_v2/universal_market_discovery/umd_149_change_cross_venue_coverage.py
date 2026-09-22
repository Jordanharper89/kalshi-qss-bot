from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_103_canonical_market_registry import CanonicalMarketRegistry
from .umd_147_observation_change_impact_registry import ObservationChangeImpactRegistry
from .umd_148_change_topology_projection import verify_umd_148_change_topology_projection

UMD_149_BUILD_ID="UMD-149"
UMD_149_REVISION="UMD_149_CHANGE_CROSS_VENUE_COVERAGE_V1"
UMD_149_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class ChangeMarketVenueCoverage:
    canonical_market_id:str
    venue_keys:Tuple[str,...]
    venue_market_ids:Tuple[Tuple[str,str],...]

    def __post_init__(self):
        object.__setattr__(self,"venue_keys",tuple(self.venue_keys))
        object.__setattr__(self,"venue_market_ids",tuple(self.venue_market_ids))
        if self.venue_keys!=tuple(sorted(set(self.venue_keys))):
            raise ValueError("venue_keys must be unique and sorted")
        if self.venue_market_ids!=tuple(sorted(set(self.venue_market_ids))):
            raise ValueError("venue_market_ids must be unique and sorted")
        if tuple(sorted({v for v,_ in self.venue_market_ids}))!=self.venue_keys:
            raise ValueError("venue_keys must match venue_market_ids")

    @property
    def cross_venue(self)->bool:
        return len(self.venue_keys)>1

    @property
    def coverage_hash(self)->str:
        return deterministic_sha256({
            "canonical_market_id":self.canonical_market_id,
            "venue_keys":self.venue_keys,
            "venue_market_ids":self.venue_market_ids,
        })

@dataclass(frozen=True,slots=True)
class ChangeCrossVenueCoverage:
    change_hash:str
    markets:Tuple[ChangeMarketVenueCoverage,...]
    missing_market_ids:Tuple[str,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"markets",tuple(self.markets))
        object.__setattr__(self,"missing_market_ids",tuple(self.missing_market_ids))
        if self.markets!=tuple(sorted(self.markets,key=lambda m:(m.canonical_market_id,m.coverage_hash))):
            raise ValueError("markets must be deterministically sorted")
        if self.missing_market_ids!=tuple(sorted(set(self.missing_market_ids))):
            raise ValueError("missing_market_ids must be unique and sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_149_BUILD_ID:
            raise ValueError("lineage must belong to UMD-149")

    def cross_venue_market_ids(self)->Tuple[str,...]:
        return tuple(m.canonical_market_id for m in self.markets if m.cross_venue)

    @property
    def coverage_hash(self)->str:
        return deterministic_sha256({
            "change_hash":self.change_hash,
            "market_hashes":tuple(m.coverage_hash for m in self.markets),
            "missing_market_ids":self.missing_market_ids,
            "lineage":self.lineage,
        })

class ChangeCrossVenueCoverageBuilder:
    __slots__=("impact_registry","market_registry")

    def __init__(self,impact_registry:ObservationChangeImpactRegistry,market_registry:CanonicalMarketRegistry):
        if not isinstance(impact_registry,ObservationChangeImpactRegistry):
            raise TypeError("impact_registry must be ObservationChangeImpactRegistry")
        if not isinstance(market_registry,CanonicalMarketRegistry):
            raise TypeError("market_registry must be CanonicalMarketRegistry")
        self.impact_registry=impact_registry
        self.market_registry=market_registry

    def build(self,change_hash:str,*,lineage:ImmutableLineage)->ChangeCrossVenueCoverage:
        market_ids=tuple(sorted({
            market_id for market_id,changes in self.impact_registry.market_index.items()
            if change_hash in changes
        }))
        result=[]; missing=[]

        for market_id in market_ids:
            record=self.market_registry.get(market_id)
            if record is None:
                missing.append(market_id)
                continue
            pairs=tuple(sorted({
                (binding.venue_key,binding.venue_market_id)
                for binding in record.venue_bindings
            }))
            venues=tuple(sorted({v for v,_ in pairs}))
            result.append(ChangeMarketVenueCoverage(market_id,venues,pairs))

        result.sort(key=lambda m:(m.canonical_market_id,m.coverage_hash))
        return ChangeCrossVenueCoverage(change_hash,tuple(result),tuple(sorted(missing)),lineage)

def build_umd_149_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_149_BUILD_ID,"revision":UMD_149_REVISION,
        "schema_version":UMD_149_SCHEMA_VERSION,"upstream_builds":("UMD-103","UMD-147","UMD-148"),
        "mode":"deterministic_read_only_change_cross_venue_coverage",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_149_change_cross_venue_coverage()->bool:
    if verify_umd_148_change_topology_projection() is not True:
        return False
    m=build_umd_149_certification_manifest()
    return m["build_id"]=="UMD-149" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
