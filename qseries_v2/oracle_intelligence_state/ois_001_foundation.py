from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OIS_001_BUILD_ID="OIS-001"
OIS_001_REVISION="OIS_001_INTELLIGENCE_STATE_FOUNDATION_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True)
class IntelligenceStatePolicy:
    deterministic:bool=True
    read_only:bool=True
    terminal_dependency:bool=False
    execution_allowed:bool=False
    publication_allowed:bool=False
    upstream_mutation:bool=False

@dataclass(frozen=True)
class IntelligenceStateIdentity:
    subject_id:str
    source_state_hash:str
    lineage_hash:str
    state_id:str

def build_intelligence_state_identity(subject_id,source_state_hash,lineage_hash):
    if not subject_id or len(source_state_hash)!=64 or len(lineage_hash)!=64:
        raise ValueError("subject and sha256 lineage required")
    raw={"subject_id":subject_id,"source_state_hash":source_state_hash,"lineage_hash":lineage_hash}
    return IntelligenceStateIdentity(subject_id,source_state_hash,lineage_hash,"ois:"+_h(raw))

def build_ois_001_certification_manifest():
    return MappingProxyType({
        "build_id":OIS_001_BUILD_ID,
        "revision":OIS_001_REVISION,
        "deterministic":True,
        "read_only":True,
        "terminal_dependency":False,
        "execution":False,
        "publication":False,
    })

def verify_ois_001_intelligence_state_foundation():
    p=IntelligenceStatePolicy()
    x=build_intelligence_state_identity("btc","a"*64,"b"*64)
    return p.deterministic and p.read_only and not p.terminal_dependency and not p.execution_allowed and x.state_id.startswith("ois:")
