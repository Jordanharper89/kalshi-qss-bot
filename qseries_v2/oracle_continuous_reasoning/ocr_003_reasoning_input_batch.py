from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json

OCR_003_BUILD_ID="OCR-003"
OCR_003_REVISION="OCR_003_REASONING_INPUT_BATCH_ASSEMBLY_V1"

def _h(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,default=str).encode()).hexdigest()

@dataclass(frozen=True)
class ReasoningObservation:
    observation_id:str
    source_id:str
    event_type:str
    market_ticker:str
    payload:tuple[tuple[str,str],...]
    record_hash:str

@dataclass(frozen=True)
class ReasoningInputBatch:
    observations:tuple[ReasoningObservation,...]
    observation_count:int
    market_count:int
    batch_hash:str
    read_only:bool=True

def _pick(row,*names):
    for n in names:
        if n in row and row[n] is not None: return row[n]
    return ""

def materialize_reasoning_observation(row):
    oid=str(_pick(row,"observation_id","id")).strip()
    if not oid: raise ValueError("observation_id required")
    source=str(_pick(row,"source_id","source","adapter_id")).strip()
    payload=_pick(row,"payload","observation_payload","data")
    if not isinstance(payload,dict): payload={"value":payload}
    event=str(_pick(payload,"event_type","type") or _pick(row,"observation_type","event_type")).strip()
    ticker=str(_pick(payload,"source_market_id","market_ticker","ticker") or _pick(row,"market_id","market_ticker")).strip()
    canonical=tuple((str(k),json.dumps(payload[k],sort_keys=True,separators=(",",":"),default=str)) for k in sorted(payload))
    raw={"observation_id":oid,"source_id":source,"event_type":event,"market_ticker":ticker,"payload":canonical}
    return ReasoningObservation(oid,source,event,ticker,canonical,_h(raw))

def assemble_reasoning_input_batch(rows):
    obs=tuple(sorted((materialize_reasoning_observation(dict(r)) for r in rows),key=lambda x:(x.market_ticker,x.observation_id)))
    if not obs: raise ValueError("reasoning observations required")
    if len({x.observation_id for x in obs})!=len(obs): raise ValueError("duplicate observation_id")
    raw={"record_hashes":[x.record_hash for x in obs],"count":len(obs)}
    return ReasoningInputBatch(obs,len(obs),len({x.market_ticker for x in obs if x.market_ticker}),_h(raw),True)

def verify_ocr_003_reasoning_input_batch_assembly():
    b=assemble_reasoning_input_batch(({"observation_id":"o1","source_id":"s","payload":{"market_ticker":"A","event_type":"ticker","x":1}},))
    return b.observation_count==1 and b.market_count==1 and b.read_only
