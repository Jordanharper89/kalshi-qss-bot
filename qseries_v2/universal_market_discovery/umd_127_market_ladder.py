from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Iterable, Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_109_market_semantic_profile import MarketSemanticProfile
from .umd_110_market_family_resolution import MarketFamily
from .umd_126_impact_coverage_registry import verify_umd_126_impact_coverage_registry

UMD_127_BUILD_ID="UMD-127"
UMD_127_REVISION="UMD_127_MARKET_LADDER_MODEL_V1"
UMD_127_SCHEMA_VERSION="1.0.0"

PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")
LADDER_OPERATORS=("above","at-least","below","at-most")

@dataclass(frozen=True,slots=True)
class LadderRung:
    canonical_market_id:str
    threshold:str
    threshold_decimal:str
    operator:str
    profile_hash:str

    def __post_init__(self):
        if self.operator not in LADDER_OPERATORS:
            raise ValueError("unsupported ladder operator")
        try:
            parsed=Decimal(self.threshold)
        except (InvalidOperation,ValueError):
            raise ValueError("threshold must be decimal-compatible")
        normalized=format(parsed.normalize(),"f")
        if "." in normalized:
            normalized=normalized.rstrip("0").rstrip(".")
        if normalized=="-0":
            normalized="0"
        if self.threshold_decimal!=normalized:
            raise ValueError("threshold_decimal does not match threshold")

    @property
    def rung_hash(self)->str:
        return deterministic_sha256({
            "canonical_market_id":self.canonical_market_id,
            "threshold_decimal":self.threshold_decimal,
            "operator":self.operator,
            "profile_hash":self.profile_hash,
        })

@dataclass(frozen=True,slots=True)
class MarketLadder:
    family_key:str
    operator:str
    rungs:Tuple[LadderRung,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"rungs",tuple(self.rungs))
        if not self.rungs:
            raise ValueError("market ladder requires at least one rung")
        if any(r.operator!=self.operator for r in self.rungs):
            raise ValueError("all rungs must use ladder operator")
        expected=tuple(sorted(
            self.rungs,
            key=lambda r:(Decimal(r.threshold_decimal),r.canonical_market_id),
        ))
        if expected!=self.rungs:
            raise ValueError("rungs must be sorted by numeric threshold")
        thresholds=[r.threshold_decimal for r in self.rungs]
        if len(thresholds)!=len(set(thresholds)):
            raise ValueError("duplicate threshold in ladder")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_127_BUILD_ID:
            raise ValueError("lineage must belong to UMD-127")
        required={r.profile_hash for r in self.rungs}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every rung profile hash")

    def market_at_threshold(self,threshold:str)->str|None:
        try:
            target=Decimal(threshold)
        except (InvalidOperation,ValueError):
            return None
        for rung in self.rungs:
            if Decimal(rung.threshold_decimal)==target:
                return rung.canonical_market_id
        return None

    @property
    def ladder_hash(self)->str:
        return deterministic_sha256({
            "family_key":self.family_key,
            "operator":self.operator,
            "rung_hashes":tuple(r.rung_hash for r in self.rungs),
            "lineage":self.lineage,
        })

class MarketLadderBuilder:
    __slots__=()

    def build(
        self,
        family:MarketFamily,
        profiles:Iterable[MarketSemanticProfile],
        *,
        lineage:ImmutableLineage,
    )->MarketLadder:
        if not isinstance(family,MarketFamily):
            raise TypeError("family must be MarketFamily")
        ps=tuple(profiles)
        if any(not isinstance(p,MarketSemanticProfile) for p in ps):
            raise TypeError("profiles must contain MarketSemanticProfile")

        members=set(family.member_market_ids)
        selected=[p for p in ps if p.canonical_market_id in members]
        if {p.canonical_market_id for p in selected}!=members:
            raise ValueError("profiles must cover every family member")

        rungs=[]
        operator=None
        for profile in selected:
            thresholds=profile.values("threshold")
            operators=profile.values("operator")
            if len(thresholds)!=1 or len(operators)!=1:
                raise ValueError("ladder profile requires exactly one threshold and one operator")
            op=operators[0]
            if op not in LADDER_OPERATORS:
                raise ValueError("unsupported ladder operator")
            if operator is None:
                operator=op
            elif operator!=op:
                raise ValueError("mixed operators cannot form one ladder")
            parsed=Decimal(thresholds[0])
            normalized=format(parsed.normalize(),"f")
            if "." in normalized:
                normalized=normalized.rstrip("0").rstrip(".")
            if normalized=="-0":
                normalized="0"
            rungs.append(LadderRung(
                profile.canonical_market_id,
                thresholds[0],
                normalized,
                op,
                profile.profile_hash,
            ))

        rungs.sort(key=lambda r:(Decimal(r.threshold_decimal),r.canonical_market_id))
        return MarketLadder(family.family_key,operator,tuple(rungs),lineage)

def build_umd_127_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_127_BUILD_ID,"revision":UMD_127_REVISION,
        "schema_version":UMD_127_SCHEMA_VERSION,"upstream_builds":("UMD-109","UMD-110","UMD-126"),
        "mode":"deterministic_read_only_market_ladder_model",
        "ladder_operators":LADDER_OPERATORS,
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_127_market_ladder_model()->bool:
    if verify_umd_126_impact_coverage_registry() is not True:
        return False
    m=build_umd_127_certification_manifest()
    return m["build_id"]=="UMD-127" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
