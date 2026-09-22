from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .osr_001_foundation import ScientificReasoningInput,verify_scientific_reasoning_input

OSR_002_BUILD_ID="OSR-002"
OSR_002_REVISION="OSR_002_HYPOTHESIS_FORMATION_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True)
class ScientificHypothesis:
    hypothesis_id:str
    statement:str
    mechanism:str
    falsifier:str
    prior_probability:float
    hypothesis_hash:str

def form_hypothesis(reasoning_input,hypothesis_id,statement,mechanism,falsifier,prior_probability):
    if not verify_scientific_reasoning_input(reasoning_input):
        raise ValueError("invalid scientific reasoning input")
    if not all(str(x).strip() for x in (hypothesis_id,statement,mechanism,falsifier)):
        raise ValueError("complete falsifiable hypothesis required")
    p=float(prior_probability)
    if not 0<p<1: raise ValueError("prior probability must be between zero and one")
    raw={"input_hash":reasoning_input.input_hash,"hypothesis_id":hypothesis_id,"statement":statement,"mechanism":mechanism,"falsifier":falsifier,"prior_probability":p}
    return ScientificHypothesis(hypothesis_id,statement,mechanism,falsifier,p,_h(raw))

def build_osr_002_certification_manifest():
    return MappingProxyType({"build_id":OSR_002_BUILD_ID,"revision":OSR_002_REVISION,"requires_falsifier":True,"requires_mechanism":True,"execution":False})

def verify_osr_002_hypothesis_formation():
    from .osr_001_foundation import build_scientific_reasoning_input
    i=build_scientific_reasoning_input("a"*64,"why")
    h=form_hypothesis(i,"h1","Entity action caused repricing","information propagation","No temporal precedence",.4)
    return len(h.hypothesis_hash)==64 and h.falsifier=="No temporal precedence"
