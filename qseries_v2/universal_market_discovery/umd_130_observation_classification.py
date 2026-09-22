from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_109_market_semantic_profile import semantic_key
from .umd_115_observation_impact import OBSERVATION_FIELDS
from .umd_129_market_topology import verify_umd_129_market_topology_registry

UMD_130_BUILD_ID="UMD-130"
UMD_130_REVISION="UMD_130_OBSERVATION_CLASSIFICATION_V1"
UMD_130_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

OBSERVATION_DOMAINS=(
    "weather",
    "politics",
    "economics",
    "central-banking",
    "corporate",
    "regulatory",
    "blockchain",
    "energy",
    "geopolitics",
    "sports",
    "science",
    "space",
    "health",
    "technology",
    "legal",
    "other",
)

DOMAIN_ALIASES=MappingProxyType({
    "weather":"weather",
    "climate":"weather",
    "politics":"politics",
    "political":"politics",
    "election":"politics",
    "economics":"economics",
    "economic":"economics",
    "macro":"economics",
    "macroeconomics":"economics",
    "central-banking":"central-banking",
    "central-bank":"central-banking",
    "federal-reserve":"central-banking",
    "fed":"central-banking",
    "corporate":"corporate",
    "company":"corporate",
    "earnings":"corporate",
    "regulatory":"regulatory",
    "regulation":"regulatory",
    "blockchain":"blockchain",
    "crypto":"blockchain",
    "on-chain":"blockchain",
    "energy":"energy",
    "geopolitics":"geopolitics",
    "geopolitical":"geopolitics",
    "sports":"sports",
    "sport":"sports",
    "science":"science",
    "scientific":"science",
    "space":"space",
    "health":"health",
    "medical":"health",
    "technology":"technology",
    "tech":"technology",
    "legal":"legal",
    "law":"legal",
    "other":"other",
})

def canonical_observation_domain(value:str)->str:
    key=semantic_key(value)
    domain=DOMAIN_ALIASES.get(key)
    if domain is None:
        raise ValueError("unsupported observation domain")
    return domain

@dataclass(frozen=True,slots=True)
class CanonicalObservationClassification:
    observation_id:str
    domain:str
    routing_facts:Tuple[Tuple[str,str],...]
    lineage:ImmutableLineage

    def __post_init__(self):
        if not isinstance(self.observation_id,str) or not self.observation_id.strip():
            raise ValueError("observation_id must be non-empty")
        normalized=[]
        for kind,value in self.routing_facts:
            if kind=="entity":
                raise ValueError("entity facts must be resolved by UMD-131")
            if kind not in OBSERVATION_FIELDS:
                raise ValueError("unsupported routing fact kind")
            normalized.append((kind,semantic_key(value)))
        normalized=tuple(sorted(set(normalized)))
        object.__setattr__(self,"domain",canonical_observation_domain(self.domain))
        object.__setattr__(self,"routing_facts",normalized)
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_130_BUILD_ID:
            raise ValueError("lineage must belong to UMD-130")

    @property
    def classification_hash(self)->str:
        return deterministic_sha256({
            "observation_id":self.observation_id,
            "domain":self.domain,
            "routing_facts":self.routing_facts,
            "lineage":self.lineage,
        })

class ObservationClassifier:
    __slots__=()

    def classify(
        self,
        observation_id:str,
        domain:str,
        routing_facts:Iterable[tuple[str,str]]=(),
        *,
        lineage:ImmutableLineage,
    )->CanonicalObservationClassification:
        return CanonicalObservationClassification(
            observation_id,
            domain,
            tuple(routing_facts),
            lineage,
        )

def build_umd_130_certification_manifest():
    data={
        "subsystem_id":"UMD",
        "build_id":UMD_130_BUILD_ID,
        "revision":UMD_130_REVISION,
        "schema_version":UMD_130_SCHEMA_VERSION,
        "upstream_builds":("UMD-109","UMD-115","UMD-129"),
        "mode":"deterministic_read_only_observation_classification",
        "observation_domains":OBSERVATION_DOMAINS,
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,
        "persistence_enabled":False,
        "mutation_enabled":False,
        "publication_enabled":False,
        "execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_130_observation_classification()->bool:
    if verify_umd_129_market_topology_registry() is not True:
        return False
    m=build_umd_130_certification_manifest()
    return m["build_id"]=="UMD-130" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
