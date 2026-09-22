from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple
from .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID, ImmutableLineage, deterministic_sha256
from .umd_104_registry_snapshot import RegistrySnapshot, verify_umd_104_registry_snapshot

UMD_105_BUILD_ID="UMD-105"; UMD_105_REVISION="UMD_105_REGISTRY_DIFF_V1"; UMD_105_SCHEMA_VERSION="1.0.0"
PROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")

@dataclass(frozen=True,slots=True)
class RegistryDiff:
    previous_snapshot_hash:str
    current_snapshot_hash:str
    added_ids:Tuple[str,...]
    removed_ids:Tuple[str,...]
    changed_ids:Tuple[str,...]
    unchanged_ids:Tuple[str,...]
    lineage:ImmutableLineage
    def __post_init__(self):
        for n in ("added_ids","removed_ids","changed_ids","unchanged_ids"): object.__setattr__(self,n,tuple(getattr(self,n)))
        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_105_BUILD_ID: raise ValueError("lineage must belong to UMD-105")
        required={self.previous_snapshot_hash,self.current_snapshot_hash}
        if not required.issubset(set(self.lineage.parent_hashes)): raise ValueError("lineage must include both snapshot hashes")
    def to_canonical_dict(self):
        return {"previous_snapshot_hash":self.previous_snapshot_hash,"current_snapshot_hash":self.current_snapshot_hash,
                "added_ids":self.added_ids,"removed_ids":self.removed_ids,"changed_ids":self.changed_ids,"unchanged_ids":self.unchanged_ids,"lineage":self.lineage}
    @property
    def diff_hash(self): return deterministic_sha256(self.to_canonical_dict())

class RegistryDiffEngine:
    __slots__=()
    def compare(self,previous:RegistrySnapshot,current:RegistrySnapshot,*,lineage:ImmutableLineage)->RegistryDiff:
        if not isinstance(previous,RegistrySnapshot) or not isinstance(current,RegistrySnapshot): raise TypeError("previous and current must be RegistrySnapshot")
        p=dict(zip(previous.record_ids,previous.record_hashes)); c=dict(zip(current.record_ids,current.record_hashes))
        ps,cs=set(p),set(c)
        added=tuple(sorted(cs-ps)); removed=tuple(sorted(ps-cs))
        shared=ps&cs
        changed=tuple(sorted(i for i in shared if p[i]!=c[i])); unchanged=tuple(sorted(i for i in shared if p[i]==c[i]))
        return RegistryDiff(previous.snapshot_hash,current.snapshot_hash,added,removed,changed,unchanged,lineage)

def build_umd_105_certification_manifest():
    d={"subsystem_id":"UMD","build_id":UMD_105_BUILD_ID,"revision":UMD_105_REVISION,"schema_version":UMD_105_SCHEMA_VERSION,
       "upstream_builds":("UMD-104",),"mode":"deterministic_read_only_registry_diff","prohibited_capabilities":PROHIBITED_CAPABILITIES,
       "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**d,"manifest_hash":deterministic_sha256(d)})
def verify_umd_105_registry_diff()->bool:
    if verify_umd_104_registry_snapshot() is not True:return False
    m=build_umd_105_certification_manifest()
    return m["build_id"]=="UMD-105" and not any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled"))
