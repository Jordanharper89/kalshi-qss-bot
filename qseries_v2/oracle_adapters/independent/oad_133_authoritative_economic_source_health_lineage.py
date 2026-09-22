from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class EconomicSourceHealthRecord:
    provider: str
    state: str
    observation_count: int
    error_type: str|None
    error_message: str|None
    checked_at: str
    lineage_id: str
    execution_authority: bool=False

def build_source_health_lineage(provider_results):
    out=[]
    for r in tuple(provider_results):
        raw=json.dumps({
            "provider":r.provider,
            "state":r.state,
            "observation_count":r.observation_count,
            "error_type":r.error_type,
            "error_message":r.error_message,
            "checked_at":r.checked_at,
        },sort_keys=True,separators=(",",":"))
        lineage_id="economic-source-health:"+sha256(raw.encode()).hexdigest()
        out.append(EconomicSourceHealthRecord(
            r.provider,r.state,int(r.observation_count),r.error_type,r.error_message,
            r.checked_at,lineage_id,False
        ))
    return tuple(out)
