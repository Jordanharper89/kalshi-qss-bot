from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable,Mapping,Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_161_convergence_diff import ConvergenceDiff,verify_umd_161_convergence_diff

UMD_162_BUILD_ID="UMD-162"
UMD_162_REVISION="UMD_162_CONVERGENCE_CHANGE_REGISTRY_V1"
UMD_162_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

CHANGE_TYPES=("convergence-added","convergence-removed","convergence-composition-changed")

def _freeze(source):
    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})

@dataclass(frozen=True,slots=True)
class ConvergenceChangeRecord:
    change_type:str
    canonical_market_id:str
    diff_hash:str
    added_change_hashes:Tuple[str,...]
    removed_change_hashes:Tuple[str,...]

    def __post_init__(self):
        object.__setattr__(self,"added_change_hashes",tuple(self.added_change_hashes))
        object.__setattr__(self,"removed_change_hashes",tuple(self.removed_change_hashes))
        if self.change_type not in CHANGE_TYPES:
            raise ValueError("unsupported convergence change type")
        if not self.canonical_market_id:
            raise ValueError("canonical_market_id must be non-empty")
        if self.added_change_hashes!=tuple(sorted(set(self.added_change_hashes))):
            raise ValueError("added_change_hashes must be unique and sorted")
        if self.removed_change_hashes!=tuple(sorted(set(self.removed_change_hashes))):
            raise ValueError("removed_change_hashes must be unique and sorted")

    @property
    def record_hash(self)->str:
        return deterministic_sha256({
            "change_type":self.change_type,
            "canonical_market_id":self.canonical_market_id,
            "diff_hash":self.diff_hash,
            "added_change_hashes":self.added_change_hashes,
            "removed_change_hashes":self.removed_change_hashes,
        })

@dataclass(frozen=True,slots=True)
class ConvergenceChangeRegistry:
    diffs:Tuple[ConvergenceDiff,...]
    records:Tuple[ConvergenceChangeRecord,...]
    market_index:Mapping[str,Tuple[str,...]]
    type_index:Mapping[str,Tuple[str,...]]
    source_change_index:Mapping[str,Tuple[str,...]]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"diffs",tuple(self.diffs))
        object.__setattr__(self,"records",tuple(self.records))
        for name in ("market_index","type_index","source_change_index"):
            object.__setattr__(self,name,_freeze(getattr(self,name)))
        if self.diffs!=tuple(sorted(self.diffs,key=lambda d:d.diff_hash)):
            raise ValueError("diffs must be deterministically sorted")
        if self.records!=tuple(sorted(
            self.records,key=lambda r:(r.change_type,r.canonical_market_id,r.diff_hash,r.record_hash)
        )):
            raise ValueError("records must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_162_BUILD_ID:
            raise ValueError("lineage must belong to UMD-162")
        required={d.diff_hash for d in self.diffs}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include every convergence diff hash")

    def record_hashes_for_market(self,market_id:str)->Tuple[str,...]:
        return self.market_index.get(market_id,())

    def markets_for_type(self,change_type:str)->Tuple[str,...]:
        return self.type_index.get(change_type,())

    def markets_for_source_change(self,change_hash:str)->Tuple[str,...]:
        return self.source_change_index.get(change_hash,())

    @property
    def registry_hash(self)->str:
        return deterministic_sha256({
            "diff_hashes":tuple(d.diff_hash for d in self.diffs),
            "record_hashes":tuple(r.record_hash for r in self.records),
            "market_index":self.market_index,
            "type_index":self.type_index,
            "source_change_index":self.source_change_index,
            "lineage":self.lineage,
        })

class ConvergenceChangeRegistryBuilder:
    __slots__=()

    def build(
        self,
        diffs:Iterable[ConvergenceDiff],
        *,
        lineage_factory,
    )->ConvergenceChangeRegistry:
        values=tuple(diffs)
        if any(not isinstance(d,ConvergenceDiff) for d in values):
            raise TypeError("diffs must contain ConvergenceDiff")
        values=tuple(sorted(values,key=lambda d:d.diff_hash))

        records=[]
        market={}
        type_index={}
        source={}

        def add(record):
            records.append(record)
            market.setdefault(record.canonical_market_id,[]).append(record.record_hash)
            type_index.setdefault(record.change_type,[]).append(record.canonical_market_id)
            for change_hash in record.added_change_hashes+record.removed_change_hashes:
                source.setdefault(change_hash,[]).append(record.canonical_market_id)

        for diff in values:
            for market_id in diff.added_market_ids:
                add(ConvergenceChangeRecord(
                    "convergence-added",market_id,diff.diff_hash,(),()
                ))
            for market_id in diff.removed_market_ids:
                add(ConvergenceChangeRecord(
                    "convergence-removed",market_id,diff.diff_hash,(),()
                ))
            for changed in diff.changed_markets:
                add(ConvergenceChangeRecord(
                    "convergence-composition-changed",
                    changed.canonical_market_id,
                    diff.diff_hash,
                    changed.added_change_hashes,
                    changed.removed_change_hashes,
                ))

        records.sort(key=lambda r:(r.change_type,r.canonical_market_id,r.diff_hash,r.record_hash))
        for index in (market,type_index,source):
            for key,items in index.items():
                index[key]=tuple(sorted(set(items)))

        lineage=lineage_factory(tuple(d.diff_hash for d in values))
        return ConvergenceChangeRegistry(
            values,tuple(records),market,type_index,source,lineage
        )

def build_umd_162_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_162_BUILD_ID,"revision":UMD_162_REVISION,
        "schema_version":UMD_162_SCHEMA_VERSION,"upstream_builds":("UMD-161",),
        "mode":"deterministic_read_only_convergence_change_registry",
        "change_types":CHANGE_TYPES,
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_162_convergence_change_registry()->bool:
    if verify_umd_161_convergence_diff() is not True:
        return False
    m=build_umd_162_certification_manifest()
    return m["build_id"]=="UMD-162" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
