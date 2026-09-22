from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping

OSR_001_BUILD_ID="OSR-001"
OSR_001_REVISION="OSR_001_SCIENTIFIC_REASONING_FOUNDATION_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True)
class ScientificReasoningInput:
    learner_handoff_hash:str
    question:str
    context_hashes:tuple[str,...]
    input_hash:str
    read_only:bool=True

def build_scientific_reasoning_input(learner_handoff_hash,question,context_hashes=()):
    if len(learner_handoff_hash)!=64 or not str(question).strip():
        raise ValueError("certified learner handoff hash and question required")
    hashes=tuple(sorted(context_hashes))
    if any(len(x)!=64 for x in hashes):
        raise ValueError("context hashes must be sha256")
    raw={"learner_handoff_hash":learner_handoff_hash,"question":str(question).strip(),"context_hashes":hashes,"read_only":True}
    return ScientificReasoningInput(learner_handoff_hash,str(question).strip(),hashes,_h(raw),True)

def verify_scientific_reasoning_input(x):
    raw={"learner_handoff_hash":x.learner_handoff_hash,"question":x.question,"context_hashes":x.context_hashes,"read_only":True}
    return x.read_only and x.input_hash==_h(raw)

def build_osr_001_certification_manifest():
    return MappingProxyType({"build_id":OSR_001_BUILD_ID,"revision":OSR_001_REVISION,"upstream":"OCL-030 frozen boundary","reasoning":"read_only","execution":False,"publication":False})

def verify_osr_001_scientific_reasoning_foundation():
    x=build_scientific_reasoning_input("a"*64,"What best explains the observed change?",("b"*64,"c"*64))
    return verify_scientific_reasoning_input(x)
