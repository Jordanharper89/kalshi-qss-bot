from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .osr_011_uncertainty_decomposition import verify_osr_011_uncertainty_decomposition_engine
from .osr_012_information_gain_priority import verify_osr_012_information_gain_evidence_priority_engine
from .osr_013_adversarial_challenge import verify_osr_013_adversarial_hypothesis_challenge_engine
from .osr_014_alternative_synthesis import verify_osr_014_contradiction_alternative_explanation_synthesis

OSR_015_BUILD_ID="OSR-015"
OSR_015_REVISION="OSR_015_UNCERTAINTY_INFORMATION_ADVERSARIAL_CERTIFICATION_GATE_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class UncertaintyInformationAdversarialCertification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_osr_011_through_015():
    checks=(verify_osr_011_uncertainty_decomposition_engine(),verify_osr_012_information_gain_evidence_priority_engine(),verify_osr_013_adversarial_hypothesis_challenge_engine(),verify_osr_014_contradiction_alternative_explanation_synthesis())
    if not all(checks): raise RuntimeError("uncertainty/information/adversarial capability certification failed")
    builds=tuple("OSR-%03d"%i for i in range(11,16))
    raw={"builds":builds,"capability":"uncertainty_information_gain_and_adversarial_reasoning","next_capability":"decision_theory_scenario_and_counterfactual_reasoning","certified":True}
    return UncertaintyInformationAdversarialCertification(builds,raw["capability"],raw["next_capability"],_h(raw))

def build_osr_015_certification_manifest():
    c=certify_osr_011_through_015()
    return MappingProxyType({"build_id":OSR_015_BUILD_ID,"revision":OSR_015_REVISION,"capability":c.capability,"next_capability":c.next_capability,"certified":True,"execution":False,"publication":False})

def verify_osr_015_uncertainty_information_adversarial_certification_gate():
    c=certify_osr_011_through_015()
    return c.certified and len(c.builds)==5 and c.next_capability=="decision_theory_scenario_and_counterfactual_reasoning"
