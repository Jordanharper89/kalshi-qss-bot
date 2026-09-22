from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import importlib,json

OCR_004_BUILD_ID="OCR-004"
OCR_004_REVISION="OCR_004_FROZEN_SCIENTIFIC_REASONING_ACTIVATION_BRIDGE_V1"

def _h(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class ScientificReasoningActivationEnvelope:
    batch_hash:str
    observation_count:int
    market_count:int
    frozen_reasoning_boundary:str
    frozen_state_boundary:str
    reasoning_ready:bool
    execution_authority:bool
    envelope_hash:str

def build_scientific_reasoning_activation_envelope(batch):
    osr=importlib.import_module("qseries_v2.oracle_scientific_reasoning.osr_030_final_freeze")
    ois=importlib.import_module("qseries_v2.oracle_intelligence_state.ois_055_final_freeze")
    if getattr(osr,"verify_osr_030_scientific_reasoning_final_certification_freeze")() is not True:
        raise RuntimeError("OSR-030 frozen boundary failed")
    if getattr(ois,"verify_ois_055_final_production_certification_freeze")() is not True:
        raise RuntimeError("OIS-055 frozen boundary failed")
    if not getattr(batch,"read_only",False) or getattr(batch,"observation_count",0)<1:
        raise ValueError("certified read-only reasoning batch required")
    raw={"batch_hash":batch.batch_hash,"observation_count":batch.observation_count,"market_count":batch.market_count,
         "frozen_reasoning_boundary":"OSR-030","frozen_state_boundary":"OIS-055","reasoning_ready":True,"execution_authority":False}
    return ScientificReasoningActivationEnvelope(raw["batch_hash"],raw["observation_count"],raw["market_count"],
        raw["frozen_reasoning_boundary"],raw["frozen_state_boundary"],True,False,_h(raw))

def verify_ocr_004_frozen_scientific_reasoning_activation_bridge():
    from .ocr_003_reasoning_input_batch import assemble_reasoning_input_batch
    b=assemble_reasoning_input_batch(({"observation_id":"o1","payload":{"market_ticker":"A","event_type":"ticker"}},))
    e=build_scientific_reasoning_activation_envelope(b)
    return e.reasoning_ready and not e.execution_authority and e.frozen_reasoning_boundary=="OSR-030"
