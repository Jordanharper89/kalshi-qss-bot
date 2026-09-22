from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ois_003_canonical_state import CanonicalOracleIntelligenceState,verify_canonical_intelligence_state

OIS_004_BUILD_ID="OIS-004"
OIS_004_REVISION="OIS_004_READ_ONLY_QUERY_SNAPSHOT_V1"

@dataclass(frozen=True)
class IntelligenceStateSnapshot:
    states:tuple[CanonicalOracleIntelligenceState,...]
    subject_index:tuple[tuple[str,int],...]
    snapshot_hash:str
    read_only:bool=True

def build_intelligence_state_snapshot(states):
    rows=tuple(sorted(states,key=lambda x:x.subject_id))
    if not rows:
        raise ValueError("canonical states required")
    if len({x.subject_id for x in rows})!=len(rows):
        raise ValueError("duplicate subject state")
    if not all(verify_canonical_intelligence_state(x) for x in rows):
        raise ValueError("invalid canonical state")
    index=tuple((x.subject_id,i) for i,x in enumerate(rows))
    raw=[{"subject_id":x.subject_id,"canonical_hash":x.canonical_hash} for x in rows]
    digest=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return IntelligenceStateSnapshot(rows,index,digest,True)

def query_intelligence_state(snapshot,subject_id):
    for subject,index in snapshot.subject_index:
        if subject==subject_id:
            return snapshot.states[index]
    return None

def build_ois_004_certification_manifest():
    return MappingProxyType({
        "build_id":OIS_004_BUILD_ID,
        "revision":OIS_004_REVISION,
        "surface":"read_only_query_snapshot",
        "terminal_safe":True,
        "api_safe":True,
        "execution":False,
    })

def verify_ois_004_read_only_query_snapshot():
    from .ois_002_osr_intake_boundary import build_osr_state_intake
    from .ois_003_canonical_state import assemble_canonical_intelligence_state
    a=assemble_canonical_intelligence_state(build_osr_state_intake("a","supported",.8,.9,.1,False,"a"*64),"b"*64)
    s=build_intelligence_state_snapshot((a,))
    return s.read_only and query_intelligence_state(s,"a").subject_id=="a"
