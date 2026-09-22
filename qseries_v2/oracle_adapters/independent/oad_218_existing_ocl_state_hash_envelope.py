from __future__ import annotations
from dataclasses import asdict,is_dataclass,dataclass
from hashlib import sha256
import json

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

def _normalize(value):
    if is_dataclass(value):
        return _normalize(asdict(value))
    if isinstance(value,dict):
        return {str(k):_normalize(v) for k,v in sorted(value.items(),key=lambda x:str(x[0]))}
    if isinstance(value,(list,tuple)):
        return [_normalize(v) for v in value]
    return value

def certified_state_hash(capability,state):
    if state is None:
        raise ValueError("physical certified state required")
    body={"capability":str(capability),"state":_normalize(state)}
    return sha256(json.dumps(body,sort_keys=True,separators=(",",":"),default=str).encode("utf-8")).hexdigest()

@dataclass(frozen=True,slots=True)
class StateHashEnvelope:
    capability:str
    state_hash:str
    evidence_present:bool=True
    fabricated:bool=False
    read_only:bool=True
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def envelope(capability,state):
    return StateHashEnvelope(str(capability),certified_state_hash(capability,state))
