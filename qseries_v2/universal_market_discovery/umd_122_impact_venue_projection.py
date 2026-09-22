from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_103_canonical_market_registry import CanonicalMarketRegistry
from .umd_119_impact_provenance import ImpactProvenanceBundle
from .umd_121_impact_family_projection import verify_umd_121_impact_family_projection

UMD_122_BUILD_ID="UMD-122"
UMD_122_REVISION="UMD_122_IMPACT_VENUE_PROJECTION_V1"
UMD_122_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class VenueImpactBinding:
    venue_key:str
    venue_market_id:str
    canonical_market_id:str
    direct:bool

    @property
    def binding_hash(self)->str:
        return deterministic_sha256({
            "venue_key":self.venue_key,
            "venue_market_id":self.venue_market_id,
            "canonical_market_id":self.canonical_market_id,
            "direct":self.direct,
        })

@dataclass(frozen=True,slots=True)
class VenueImpactProjection:
    observation_hash:str
    bindings:Tuple[VenueImpactBinding,...]
    missing_market_ids:Tuple[str,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"bindings",tuple(self.bindings))
        object.__setattr__(self,"missing_market_ids",tuple(self.missing_market_ids))
        expected=tuple(sorted(self.bindings,key=lambda b:(b.venue_key,b.venue_market_id,b.canonical_market_id,b.direct)))
        if expected!=self.bindings:
            raise ValueError("bindings must be deterministically sorted")
        if self.missing_market_ids!=tuple(sorted(set(self.missing_market_ids))):
            raise ValueError("missing_market_ids must be unique and sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_122_BUILD_ID:
            raise ValueError("lineage must belong to UMD-122")

    def venues(self)->Tuple[str,...]:
        return tuple(sorted({b.venue_key for b in self.bindings}))

    def bindings_for_venue(self,venue_key:str)->Tuple[VenueImpactBinding,...]:
        return tuple(b for b in self.bindings if b.venue_key==venue_key)

    @property
    def projection_hash(self)->str:
        return deterministic_sha256({
            "observation_hash":self.observation_hash,
            "binding_hashes":tuple(b.binding_hash for b in self.bindings),
            "missing_market_ids":self.missing_market_ids,
            "lineage":self.lineage,
        })

class ImpactVenueProjector:
    __slots__=()

    def project(
        self,
        bundle:ImpactProvenanceBundle,
        registry:CanonicalMarketRegistry,
        *,
        lineage:ImmutableLineage,
    )->VenueImpactProjection:
        if not isinstance(bundle,ImpactProvenanceBundle):
            raise TypeError("bundle must be ImpactProvenanceBundle")
        if not isinstance(registry,CanonicalMarketRegistry):
            raise TypeError("registry must be CanonicalMarketRegistry")

        bindings=[]
        missing=[]
        for entry in bundle.entries:
            record=registry.get(entry.canonical_market_id)
            if record is None:
                missing.append(entry.canonical_market_id)
                continue
            for venue_binding in record.venue_bindings:
                bindings.append(VenueImpactBinding(
                    venue_binding.venue_key,
                    venue_binding.venue_market_id,
                    entry.canonical_market_id,
                    entry.direct,
                ))

        bindings.sort(key=lambda b:(b.venue_key,b.venue_market_id,b.canonical_market_id,b.direct))
        return VenueImpactProjection(
            bundle.observation_hash,
            tuple(bindings),
            tuple(sorted(set(missing))),
            lineage,
        )

def build_umd_122_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_122_BUILD_ID,"revision":UMD_122_REVISION,
        "schema_version":UMD_122_SCHEMA_VERSION,"upstream_builds":("UMD-103","UMD-119","UMD-121"),
        "mode":"deterministic_read_only_impact_venue_projection",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_122_impact_venue_projection()->bool:
    if verify_umd_121_impact_family_projection() is not True:
        return False
    m=build_umd_122_certification_manifest()
    return m["build_id"]=="UMD-122" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
