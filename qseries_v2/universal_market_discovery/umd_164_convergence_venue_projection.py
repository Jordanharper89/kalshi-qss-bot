from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_103_canonical_market_registry import CanonicalMarketRegistry
from .umd_163_convergence_topology_projection import ConvergenceTopologyProjection,verify_umd_163_convergence_topology_projection

UMD_164_BUILD_ID="UMD-164"
UMD_164_REVISION="UMD_164_CONVERGENCE_VENUE_PROJECTION_V1"
UMD_164_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class ConvergenceVenueBinding:
    canonical_market_id:str
    venue_key:str
    venue_market_id:str
    change_types:Tuple[str,...]

    def __post_init__(self):
        object.__setattr__(self,"change_types",tuple(self.change_types))
        if self.change_types!=tuple(sorted(set(self.change_types))):
            raise ValueError("change_types must be unique and sorted")
        if not self.canonical_market_id or not self.venue_key or not self.venue_market_id:
            raise ValueError("venue binding fields must be non-empty")

    @property
    def binding_hash(self)->str:
        return deterministic_sha256({
            "canonical_market_id":self.canonical_market_id,
            "venue_key":self.venue_key,
            "venue_market_id":self.venue_market_id,
            "change_types":self.change_types,
        })

@dataclass(frozen=True,slots=True)
class ConvergenceVenueProjection:
    bindings:Tuple[ConvergenceVenueBinding,...]
    missing_market_ids:Tuple[str,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"bindings",tuple(self.bindings))
        object.__setattr__(self,"missing_market_ids",tuple(self.missing_market_ids))
        if self.bindings!=tuple(sorted(
            self.bindings,key=lambda b:(b.canonical_market_id,b.venue_key,b.venue_market_id,b.binding_hash)
        )):
            raise ValueError("bindings must be deterministically sorted")
        if self.missing_market_ids!=tuple(sorted(set(self.missing_market_ids))):
            raise ValueError("missing_market_ids must be unique and sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_164_BUILD_ID:
            raise ValueError("lineage must belong to UMD-164")

    def venues_for_market(self,market_id:str)->Tuple[str,...]:
        return tuple(sorted({b.venue_key for b in self.bindings if b.canonical_market_id==market_id}))

    def markets_for_venue(self,venue_key:str)->Tuple[str,...]:
        return tuple(sorted({b.canonical_market_id for b in self.bindings if b.venue_key==venue_key}))

    @property
    def projection_hash(self)->str:
        return deterministic_sha256({
            "binding_hashes":tuple(b.binding_hash for b in self.bindings),
            "missing_market_ids":self.missing_market_ids,
            "lineage":self.lineage,
        })

class ConvergenceVenueProjector:
    __slots__=("market_registry",)

    def __init__(self,market_registry:CanonicalMarketRegistry):
        if not isinstance(market_registry,CanonicalMarketRegistry):
            raise TypeError("market_registry must be CanonicalMarketRegistry")
        self.market_registry=market_registry

    def project(
        self,
        topology_projection:ConvergenceTopologyProjection,
        *,
        lineage:ImmutableLineage,
    )->ConvergenceVenueProjection:
        if not isinstance(topology_projection,ConvergenceTopologyProjection):
            raise TypeError("topology_projection must be ConvergenceTopologyProjection")

        bindings=[]; missing=[]
        for market_id in topology_projection.market_ids:
            record=self.market_registry.get(market_id)
            if record is None:
                missing.append(market_id)
                continue
            types=topology_projection.market_to_change_types.get(market_id,())
            for venue in record.venue_bindings:
                bindings.append(ConvergenceVenueBinding(
                    market_id,venue.venue_key,venue.venue_market_id,types
                ))

        bindings.sort(key=lambda b:(b.canonical_market_id,b.venue_key,b.venue_market_id,b.binding_hash))
        return ConvergenceVenueProjection(tuple(bindings),tuple(sorted(missing)),lineage)

def build_umd_164_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_164_BUILD_ID,"revision":UMD_164_REVISION,
        "schema_version":UMD_164_SCHEMA_VERSION,"upstream_builds":("UMD-103","UMD-163"),
        "mode":"deterministic_read_only_convergence_venue_projection",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_164_convergence_venue_projection()->bool:
    if verify_umd_163_convergence_topology_projection() is not True:
        return False
    m=build_umd_164_certification_manifest()
    return m["build_id"]=="UMD-164" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
