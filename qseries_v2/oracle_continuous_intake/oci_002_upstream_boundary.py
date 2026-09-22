from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Mapping, Any
from .oci_001_foundation import verify_oci_001_continuous_intake_foundation

OCI_002_BUILD_ID="OCI-002"
OCI_002_REVISION="OCI_002_CERTIFIED_UPSTREAM_BOUNDARY_INVENTORY_V1"

REQUIRED_BOUNDARIES = (
    ("OAR", "qseries_v2/observation_adapter_runtime"),
    ("UMD", "qseries_v2/universal_market_discovery"),
    ("OML", "qseries_v2/oracle_memory"),
)
LIVE_SHADOW_RUNNERS = (
    "run_oracle_live_shadow_CONTINUOUS_GUARDED.py",
    "run_oracle_terminal_LIVE_READ_ONLY.py",
)

def _hash(v: object) -> str:
    return sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

def _file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()

@dataclass(frozen=True)
class UpstreamBoundaryEvidence:
    subsystem_id: str
    relative_path: str
    exists: bool
    python_file_count: int
    tree_hash: str

@dataclass(frozen=True)
class CertifiedUpstreamInventory:
    repository_root: str
    boundaries: tuple[UpstreamBoundaryEvidence, ...]
    runner_hashes: tuple[tuple[str,str], ...]
    read_only: bool
    inventory_hash: str

def inspect_upstream_boundaries(root: Path) -> CertifiedUpstreamInventory:
    root = root.resolve()
    entries=[]
    for sid, rel in REQUIRED_BOUNDARIES:
        path=root/rel
        files=tuple(sorted(p for p in path.rglob("*.py") if p.is_file())) if path.is_dir() else ()
        digest=_hash(tuple((str(p.relative_to(root)).replace("\\","/"), _file_hash(p)) for p in files))
        entries.append(UpstreamBoundaryEvidence(sid, rel, path.is_dir(), len(files), digest))
    runners=[]
    for name in LIVE_SHADOW_RUNNERS:
        p=root/name
        if p.is_file():
            runners.append((name,_file_hash(p)))
    raw={
        "repository_root":str(root),
        "boundaries":[asdict(x) for x in entries],
        "runner_hashes":runners,
        "read_only":True,
    }
    return CertifiedUpstreamInventory(str(root),tuple(entries),tuple(runners),True,_hash(raw))

def verify_inventory(inventory: CertifiedUpstreamInventory) -> bool:
    if not inventory.read_only or len(inventory.boundaries) != len(REQUIRED_BOUNDARIES):
        return False
    raw={
        "repository_root":inventory.repository_root,
        "boundaries":[asdict(x) for x in inventory.boundaries],
        "runner_hashes":list(inventory.runner_hashes),
        "read_only":inventory.read_only,
    }
    return inventory.inventory_hash == _hash(raw)

def build_oci_002_certification_manifest() -> Mapping[str,Any]:
    raw={"build_id":OCI_002_BUILD_ID,"revision":OCI_002_REVISION,"upstream":"OCI-001",
         "imports_frozen_upstream":False,"mutates_upstream":False,"network_enabled":False,
         "persistence_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**raw,"manifest_hash":_hash(raw)})

def verify_oci_002_upstream_boundary_inventory() -> bool:
    m=build_oci_002_certification_manifest()
    return verify_oci_001_continuous_intake_foundation() and not any(
        m[k] for k in ("imports_frozen_upstream","mutates_upstream","network_enabled","persistence_enabled","publication_enabled","execution_enabled")
    )
