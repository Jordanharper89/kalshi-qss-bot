from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple

from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256
from .umd_160_convergence_snapshot import ConvergenceSnapshot,verify_umd_160_convergence_snapshot

UMD_161_BUILD_ID="UMD-161"
UMD_161_REVISION="UMD_161_CONVERGENCE_DIFF_V1"
UMD_161_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class ConvergenceMarketChange:
    canonical_market_id:str
    before_change_hashes:Tuple[str,...]
    after_change_hashes:Tuple[str,...]
    added_change_hashes:Tuple[str,...]
    removed_change_hashes:Tuple[str,...]

    def __post_init__(self):
        for name in (
            "before_change_hashes","after_change_hashes",
            "added_change_hashes","removed_change_hashes"
        ):
            value=tuple(getattr(self,name))
            if value!=tuple(sorted(set(value))):
                raise ValueError(f"{name} must be unique and sorted")
            object.__setattr__(self,name,value)
        if self.added_change_hashes!=tuple(sorted(set(self.after_change_hashes)-set(self.before_change_hashes))):
            raise ValueError("added_change_hashes inconsistent with before/after")
        if self.removed_change_hashes!=tuple(sorted(set(self.before_change_hashes)-set(self.after_change_hashes))):
            raise ValueError("removed_change_hashes inconsistent with before/after")

    @property
    def change_hash(self)->str:
        return deterministic_sha256({
            "canonical_market_id":self.canonical_market_id,
            "before_change_hashes":self.before_change_hashes,
            "after_change_hashes":self.after_change_hashes,
            "added_change_hashes":self.added_change_hashes,
            "removed_change_hashes":self.removed_change_hashes,
        })

@dataclass(frozen=True,slots=True)
class ConvergenceDiff:
    before_snapshot_hash:str
    after_snapshot_hash:str
    added_market_ids:Tuple[str,...]
    removed_market_ids:Tuple[str,...]
    changed_markets:Tuple[ConvergenceMarketChange,...]
    lineage:ImmutableLineage

    def __post_init__(self):
        object.__setattr__(self,"added_market_ids",tuple(self.added_market_ids))
        object.__setattr__(self,"removed_market_ids",tuple(self.removed_market_ids))
        object.__setattr__(self,"changed_markets",tuple(self.changed_markets))
        if self.added_market_ids!=tuple(sorted(set(self.added_market_ids))):
            raise ValueError("added_market_ids must be unique and sorted")
        if self.removed_market_ids!=tuple(sorted(set(self.removed_market_ids))):
            raise ValueError("removed_market_ids must be unique and sorted")
        if set(self.added_market_ids)&set(self.removed_market_ids):
            raise ValueError("market cannot be both added and removed")
        if self.changed_markets!=tuple(sorted(
            self.changed_markets,key=lambda c:(c.canonical_market_id,c.change_hash)
        )):
            raise ValueError("changed_markets must be deterministically sorted")
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_161_BUILD_ID:
            raise ValueError("lineage must belong to UMD-161")
        required={self.before_snapshot_hash,self.after_snapshot_hash}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("lineage must include both convergence snapshots")

    @property
    def empty(self)->bool:
        return not self.added_market_ids and not self.removed_market_ids and not self.changed_markets

    @property
    def diff_hash(self)->str:
        return deterministic_sha256({
            "before_snapshot_hash":self.before_snapshot_hash,
            "after_snapshot_hash":self.after_snapshot_hash,
            "added_market_ids":self.added_market_ids,
            "removed_market_ids":self.removed_market_ids,
            "changed_market_hashes":tuple(c.change_hash for c in self.changed_markets),
            "lineage":self.lineage,
        })

class ConvergenceDiffer:
    __slots__=()

    def diff(
        self,
        before:ConvergenceSnapshot,
        after:ConvergenceSnapshot,
        *,
        lineage:ImmutableLineage,
    )->ConvergenceDiff:
        if not isinstance(before,ConvergenceSnapshot) or not isinstance(after,ConvergenceSnapshot):
            raise TypeError("before and after must be ConvergenceSnapshot")
        if after.as_of<before.as_of:
            raise ValueError("after snapshot must not precede before snapshot")

        before_map={r.canonical_market_id:r for r in before.records}
        after_map={r.canonical_market_id:r for r in after.records}

        before_ids=set(before_map)
        after_ids=set(after_map)
        added=tuple(sorted(after_ids-before_ids))
        removed=tuple(sorted(before_ids-after_ids))

        changed=[]
        for market_id in sorted(before_ids&after_ids):
            b=before_map[market_id].change_hashes
            a=after_map[market_id].change_hashes
            if b==a:
                continue
            changed.append(ConvergenceMarketChange(
                market_id,b,a,
                tuple(sorted(set(a)-set(b))),
                tuple(sorted(set(b)-set(a))),
            ))

        return ConvergenceDiff(
            before.snapshot_hash,
            after.snapshot_hash,
            added,
            removed,
            tuple(changed),
            lineage,
        )

def build_umd_161_certification_manifest():
    data={
        "subsystem_id":"UMD","build_id":UMD_161_BUILD_ID,"revision":UMD_161_REVISION,
        "schema_version":UMD_161_SCHEMA_VERSION,"upstream_builds":("UMD-160",),
        "mode":"deterministic_read_only_convergence_diff",
        "semantics":"structural_convergence_change_detection_only",
        "prohibited_capabilities":PROHIBITED_CAPABILITIES,
        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,
        "publication_enabled":False,"execution_enabled":False,
    }
    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})

def verify_umd_161_convergence_diff()->bool:
    if verify_umd_160_convergence_snapshot() is not True:
        return False
    m=build_umd_161_certification_manifest()
    return m["build_id"]=="UMD-161" and not any(
        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
    )
