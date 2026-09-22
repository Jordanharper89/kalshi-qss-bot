from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ois_006_state_update import IntelligenceStateUpdate
OIS_007_BUILD_ID="OIS-007";OIS_007_REVISION="OIS_007_STATE_VERSIONING_TRANSITION_LINEAGE_V1"
@dataclass(frozen=True)
class StateVersion:
    subject_id:str;version:int;state_hash:str;parent_state_hash:str|None;transition_hash:str;version_hash:str
def build_state_version(update,previous_version=None):
    if not isinstance(update,IntelligenceStateUpdate):raise ValueError("certified update required")
    version=1 if previous_version is None else previous_version.version+1
    parent=None if previous_version is None else previous_version.state_hash
    if previous_version is not None and previous_version.subject_id!=update.subject_id:raise ValueError("subject lineage mismatch")
    if previous_version is not None and previous_version.state_hash!=update.previous_hash:raise ValueError("parent state mismatch")
    raw={"subject":update.subject_id,"version":version,"state":update.next_hash,"parent":parent,"transition":update.update_hash}
    h=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return StateVersion(update.subject_id,version,update.next_hash,parent,update.update_hash,h)
def build_ois_007_certification_manifest():return MappingProxyType({"build_id":OIS_007_BUILD_ID,"revision":OIS_007_REVISION,"lineage":"append_only_version_chain","execution":False})
def verify_ois_007_state_versioning_transition_lineage():
    u=IntelligenceStateUpdate("a"*64,"b"*64,"x",True,1,"c"*64);v=build_state_version(u)
    return v.version==1 and v.parent_state_hash is None
