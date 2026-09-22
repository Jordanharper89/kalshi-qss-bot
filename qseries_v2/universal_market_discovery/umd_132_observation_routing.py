from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_103_canonical_market_registry import CanonicalMarketRegistry
from .umd_111_semantic_registry import SemanticRegistry
from .umd_114_dependency_registry import DependencyRegistry
from .umd_115_observation_impact import ObservationDescriptor,ObservationImpactMapper
from .umd_130_observation_classification import CanonicalObservationClassification
from .umd_131_observation_entity_resolution import ObservationEntityResolution,verify_umd_131_observation_entity_resolution

UMD_132_BUILD_ID="UMD-132"
UMD_132_REVISION="UMD_132_OBSERVATION_ROUTING_V1"
UMD_132_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class RoutedVenueBinding:
    venue_key:str
    venue_market_id:str
    canonical_market_id:str

    @property
    def binding_hash(self)->str:
        return deterministic_sha256({
            "venue_key":self.venue_key,
            "venue_market_id":self.venue_market_id,
            "canonical_market_id":self.canonical_market_id,
        })

@dataclass(frozen=True,slots=True)
class ObservationRoute:
    observation_id:str
    domain:str
    classification_hash:str
    entity_resolution_hash:str
    routing_facts:Tuple[Tuple[str,str],...]
    market_ids:Tuple[str,...]
    family_keys:Tuple[str,...]
    venue_bindings:Tuple[RoutedVenueBinding,...]
    matched_dependencies:Tuple[Tuple[str,str,Tuple[str,...]],...]
    unresolved_entities:Tuple[Tuple[str,str],...]
    missing_market_ids:Tuple[str,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        for name in ("routing_facts","market_ids","family_keys","venue_bindings","matched_dependencies","unresolved_entities","missing_market_ids"):
            object.__setattr__(self,name,tuple(getattr(self,name)))
        if self.routing_facts!=tuple(sorted(set(self.routing_facts))):
            raise ValueError("routing_facts must be unique and sorted")
        if self.market_ids!=tuple(sorted(set(self.market_ids))):
            raise ValueError("market_ids must be unique and sorted")
        if self.family_keys!=tuple(sorted(set(self.family_keys))):
            raise ValueError("family_keys must be unique and sorted")
        if self.venue_bindings!=tuple(sorted(
            self.venue_bindings,
            key=lambda b:(b.venue_key,b.venue_market_id,b.canonical_market_id)
        )):
            raise ValueError("venue_bindings must be deterministically sorted")
        if self.unresolved_entities!=tuple(sorted(set(self.unresolved_entities))):
            raise ValueError("unresolved_entities must be unique and sorted")
        if self.missing_market_ids!=tuple(sorted(set(self.missing_market_ids))):
            raise ValueError("missing_market_ids must be unique and sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_132_BUILD_ID:
            raise ValueError("lineage must belong to UMD-132")
        required={self.classification_hash,self.entity_resolution_hash}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include classification and entity resolution hashes")

    def venues(self)->Tuple[str,...]:
        return tuple(sorted({b.venue_key for b in self.venue_bindings}))

    def markets_for_venue(self,venue_key:str)->Tuple[str,...]:
        return tuple(sorted({
            b.canonical_market_id for b in self.venue_bindings
            if b.venue_key==venue_key
        }))

    @property
    def route_hash(self)->str:
        return deterministic_sha256({
            "observation_id":self.observation_id,
            "domain":self.domain,
            "classification_hash":self.classification_hash,
            "entity_resolution_hash":self.entity_resolution_hash,
            "routing_facts":self.routing_facts,
            "market_ids":self.market_ids,
            "family_keys":self.family_keys,
            "venue_binding_hashes":tuple(b.binding_hash for b in self.venue_bindings),
            "matched_dependencies":self.matched_dependencies,
            "unresolved_entities":self.unresolved_entities,
            "missing_market_ids":self.missing_market_ids,
            "lineage":self.lineage,
        })

class ObservationRouter:
    __slots__=("dependency_registry","semantic_registry","market_registry")

    def __init__(
        self,
        dependency_registry:DependencyRegistry,
        semantic_registry:SemanticRegistry,
        market_registry:CanonicalMarketRegistry,
    ):
        if not isinstance(dependency_registry,DependencyRegistry):
            raise TypeError("dependency_registry must be DependencyRegistry")
        if not isinstance(semantic_registry,SemanticRegistry):
            raise TypeError("semantic_registry must be SemanticRegistry")
        if not isinstance(market_registry,CanonicalMarketRegistry):
            raise TypeError("market_registry must be CanonicalMarketRegistry")
        self.dependency_registry=dependency_registry
        self.semantic_registry=semantic_registry
        self.market_registry=market_registry

    def route(
        self,
        classification:CanonicalObservationClassification,
        entities:ObservationEntityResolution,
        *,
        lineage:ImmutableLineage,
    )->ObservationRoute:
        if not isinstance(classification,CanonicalObservationClassification):
            raise TypeError("classification must be CanonicalObservationClassification")
        if not isinstance(entities,ObservationEntityResolution):
            raise TypeError("entities must be ObservationEntityResolution")
        if entities.observation_id!=classification.observation_id:
            raise ValueError("classification and entity resolution observation ids do not match")
        if entities.classification_hash!=classification.classification_hash:
            raise ValueError("entity resolution does not belong to classification")

        facts=set(classification.routing_facts)
        for binding in entities.bindings:
            facts.add((binding.kind,binding.canonical_key))
        facts=tuple(sorted(facts))

        descriptor_lineage=ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-115",
            revision="UMD_115_OBSERVATION_IMPACT_MAPPING_V1",
            schema_version="1.0.0",
            parent_hashes=(classification.classification_hash,entities.resolution_hash),
            source_refs=lineage.source_refs,
            created_at=lineage.created_at,
        )
        descriptor=ObservationDescriptor(
            classification.observation_id,
            facts,
            descriptor_lineage,
        )
        impact_lineage=ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-115",
            revision="UMD_115_OBSERVATION_IMPACT_MAPPING_V1",
            schema_version="1.0.0",
            parent_hashes=(descriptor.observation_hash,),
            source_refs=lineage.source_refs,
            created_at=lineage.created_at,
        )
        direct=ObservationImpactMapper(self.dependency_registry).map(
            descriptor,
            lineage=impact_lineage,
        )

        market_ids=set(direct.market_ids)
        # If an entity is known semantically but not declared as a dependency yet,
        # preserve its known structural market connections in routing.
        for binding in entities.bindings:
            market_ids.update(binding.known_market_ids)

        family_keys=set()
        venue_bindings=[]
        missing=[]

        for market_id in sorted(market_ids):
            for family in self.semantic_registry.families:
                if market_id in family.member_market_ids:
                    family_keys.add(family.family_key)

            record=self.market_registry.get(market_id)
            if record is None:
                missing.append(market_id)
                continue
            for venue in record.venue_bindings:
                venue_bindings.append(RoutedVenueBinding(
                    venue.venue_key,
                    venue.venue_market_id,
                    market_id,
                ))

        venue_bindings.sort(key=lambda b:(b.venue_key,b.venue_market_id,b.canonical_market_id))

        return ObservationRoute(
            classification.observation_id,
            classification.domain,
            classification.classification_hash,
            entities.resolution_hash,
            facts,
            tuple(sorted(market_ids)),
            tuple(sorted(family_keys)),
            tuple(venue_bindings),
            tuple(direct.matched_dependencies),
            tuple(entities.unresolved),
            tuple(sorted(set(missing))),
            lineage,
        )

def build_umd_132_certification_manifest():
    data={
        "subsystem_id":"UMD",
        "build_id":UMD_132_BUILD_ID,
        "revision":UMD_132_REVISION,
        "schema_version":UMD_132_SCHEMA_VERSION,
        "upstream_builds":("UMD-103","UMD-111","UMD-114","UMD-115","UMD-130","UMD-131"),
        "mode":"deterministic_read_only_observation_routing",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,
        "persistence_enabled":False,
        "mutation_enabled":False,
        "publication_enabled":False,
        "execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_132_observation_routing()->bool:
    if verify_umd_131_observation_entity_resolution() is not True:
        return False
    m=build_umd_132_certification_manifest()
    return m["build_id"]=="UMD-132" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
