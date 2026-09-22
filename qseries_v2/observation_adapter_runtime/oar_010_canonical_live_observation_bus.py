from __future__ import annotations
from dataclasses import dataclass
from datetime import timezone
import hashlib,json
from typing import Any,Mapping
from .oar_003_multi_adapter_runner import MultiAdapterRunResult

BUILD_ID="OAR-010"
OAR_010_REVISION="OAR_010_CANONICAL_LIVE_OBSERVATION_BUS_V1"
READ_ONLY=True
EXECUTION_ALLOWED=False
PUBLICATION_ALLOWED=False

def _hash(v:Any)->str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True,slots=True)
class CanonicalLiveObservation:
    observation_id:str
    adapter_id:str
    provider_id:str
    capability:str
    payload:tuple[tuple[str,str],...]
    observed_at:object
    iteration_number:int
    lineage_hash:str
    observation_hash:str
    read_only:bool

@dataclass(frozen=True,slots=True)
class CanonicalLiveObservationBatch:
    iteration_number:int
    observations:tuple[CanonicalLiveObservation,...]
    observation_count:int
    batch_hash:str
    read_only:bool

class CanonicalLiveObservationBus:
    read_only=True
    execution_allowed=False
    publication_allowed=False
    def materialize(self,run_result:MultiAdapterRunResult)->CanonicalLiveObservationBatch:
        if not isinstance(run_result,MultiAdapterRunResult): raise TypeError("run_result must be MultiAdapterRunResult")
        rows=[]
        for result in run_result.results:
            if not result.success: continue
            for i,raw in enumerate(result.observations,1):
                if not isinstance(raw,Mapping): raw={"value":raw}
                payload=tuple(sorted((str(k),str(v)) for k,v in raw.items()))
                body={"adapter_id":result.adapter_id,"provider_id":result.provider_id,"capability":result.capability,"payload":payload,"observed_at":result.observed_at.astimezone(timezone.utc).isoformat(),"iteration":run_result.iteration_number,"ordinal":i}
                h=_hash(body)
                rows.append(CanonicalLiveObservation("liveobs."+h[:32],result.adapter_id,result.provider_id,result.capability,payload,result.observed_at.astimezone(timezone.utc),run_result.iteration_number,_hash({"request_id":result.request_id,"adapter_id":result.adapter_id,"provider_id":result.provider_id,"capability":result.capability}),h,True))
        rows=tuple(sorted(rows,key=lambda x:(x.adapter_id,x.capability,x.observation_hash)))
        return CanonicalLiveObservationBatch(run_result.iteration_number,rows,len(rows),_hash({"iteration":run_result.iteration_number,"hashes":tuple(x.observation_hash for x in rows)}),True)

def verify_canonical_live_observation_bus()->bool:
    assert READ_ONLY is True and EXECUTION_ALLOWED is False and PUBLICATION_ALLOWED is False
    return True
