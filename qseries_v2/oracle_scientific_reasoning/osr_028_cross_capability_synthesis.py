from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OSR_028_BUILD_ID = "OSR-028"
OSR_028_REVISION = "OSR_028_CROSS_CAPABILITY_SCIENTIFIC_REASONING_SYNTHESIS_V1"

@dataclass(frozen=True)
class CapabilityReasoningState:
    capability_id: str
    support: float
    confidence: float
    contradiction: float
    abstain: bool

@dataclass(frozen=True)
class CrossCapabilitySynthesis:
    participating_capabilities: tuple[str, ...]
    support: float
    confidence: float
    contradiction: float
    state: str
    abstain: bool
    synthesis_hash: str

def synthesize_capabilities(states, minimum_confidence=0.65):
    rows = tuple(sorted(states, key=lambda x: x.capability_id))
    if not rows:
        raise ValueError("capability states required")

    if len({x.capability_id for x in rows}) != len(rows):
        raise ValueError("duplicate capability")

    for x in rows:
        if any(not 0 <= v <= 1 for v in (x.support, x.confidence, x.contradiction)):
            raise ValueError("normalized capability values required")

    support = sum(x.support for x in rows) / len(rows)
    confidence = sum(x.confidence for x in rows) / len(rows)
    contradiction = sum(x.contradiction for x in rows) / len(rows)

    abstain = (
        any(x.abstain for x in rows)
        or confidence < minimum_confidence
        or contradiction > 0.5
    )

    state = (
        "supported"
        if not abstain and support >= 0.5
        else ("contradicted" if contradiction > 0.5 else "uncertain")
    )

    raw = [
        {
            "capability_id": x.capability_id,
            "support": x.support,
            "confidence": x.confidence,
            "contradiction": x.contradiction,
            "abstain": x.abstain,
        }
        for x in rows
    ]
    digest = sha256(
        json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    return CrossCapabilitySynthesis(
        tuple(x.capability_id for x in rows),
        support,
        confidence,
        contradiction,
        state,
        abstain,
        digest,
    )

def build_osr_028_certification_manifest():
    return MappingProxyType({
        "build_id": OSR_028_BUILD_ID,
        "revision": OSR_028_REVISION,
        "synthesis": "cross_certified_reasoning_capabilities",
        "abstention": True,
        "execution": False,
    })

def verify_osr_028_cross_capability_scientific_reasoning_synthesis():
    rows = (
        CapabilityReasoningState("bayesian", 0.9, 0.9, 0.1, False),
        CapabilityReasoningState("causal", 0.8, 0.8, 0.1, False),
    )
    return synthesize_capabilities(rows).state == "supported"
