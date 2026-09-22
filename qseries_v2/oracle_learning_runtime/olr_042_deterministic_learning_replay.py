from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json

OLR_042_BUILD_ID="OLR-042"
OLR_042_REVISION="OLR_042_DETERMINISTIC_LEARNING_REPLAY_V1"

@dataclass(frozen=True)
class LearningReplayResult:
    input_records:int
    output_records:int
    replay_hash:str
    deterministic:bool
    execution_authority:bool=False

def canonicalize_learning_records(records):
    normalized=[]
    for r in records:
        if isinstance(r,dict):
            normalized.append(dict(sorted((str(k),v) for k,v in r.items())))
        else:
            normalized.append({"value":r})
    normalized.sort(key=lambda x:json.dumps(x,sort_keys=True,separators=(",",":"),default=str))
    return tuple(normalized)

def replay_learning_records(records):
    canonical=canonicalize_learning_records(records)
    payload=json.dumps(canonical,sort_keys=True,separators=(",",":"),default=str)
    digest=sha256(payload.encode()).hexdigest()
    second=json.dumps(canonicalize_learning_records(canonical),sort_keys=True,separators=(",",":"),default=str)
    digest2=sha256(second.encode()).hexdigest()
    return LearningReplayResult(len(tuple(records)),len(canonical),digest,digest==digest2,False)

def verify_olr_042_deterministic_learning_replay():
    rows=({"b":2,"a":1},{"a":3})
    x=replay_learning_records(rows)
    return x.deterministic and len(x.replay_hash)==64 and not x.execution_authority
