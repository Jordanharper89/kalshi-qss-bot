from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OSR_008_BUILD_ID="OSR-008"
OSR_008_REVISION="OSR_008_TEMPORAL_PRECEDENCE_EVENT_SEQUENCE_REASONING_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True)
class TemporalEvent:
    event_id:str
    timestamp_ms:int
    evidence_hash:str

@dataclass(frozen=True)
class TemporalSequenceAnalysis:
    ordered_events:tuple[TemporalEvent,...]
    sequence_hash:str
    strictly_ordered:bool
    causal_precedence_pairs:tuple[tuple[str,str],...]

def analyze_temporal_sequence(events):
    rows=tuple(sorted(events,key=lambda x:(x.timestamp_ms,x.event_id)))
    if not rows: raise ValueError("temporal events required")
    if len({x.event_id for x in rows})!=len(rows): raise ValueError("duplicate event id")
    if any(len(x.evidence_hash)!=64 for x in rows): raise ValueError("evidence hash required")
    strict=all(a.timestamp_ms < b.timestamp_ms for a,b in zip(rows,rows[1:]))
    pairs=tuple((a.event_id,b.event_id) for i,a in enumerate(rows) for b in rows[i+1:] if a.timestamp_ms < b.timestamp_ms)
    raw=[{"event_id":x.event_id,"timestamp_ms":x.timestamp_ms,"evidence_hash":x.evidence_hash} for x in rows]
    return TemporalSequenceAnalysis(rows,_h(raw),strict,pairs)

def precedes(analysis,cause_event_id,effect_event_id):
    return (cause_event_id,effect_event_id) in analysis.causal_precedence_pairs

def build_osr_008_certification_manifest():
    return MappingProxyType({"build_id":OSR_008_BUILD_ID,"revision":OSR_008_REVISION,"temporal_reasoning":"deterministic_event_order","causation_claimed":False,"execution":False})

def verify_osr_008_temporal_precedence_event_sequence_reasoning():
    a=TemporalEvent("a",1000,"a"*64);b=TemporalEvent("b",2000,"b"*64)
    x=analyze_temporal_sequence((b,a))
    return x.strictly_ordered and precedes(x,"a","b") and not precedes(x,"b","a")
