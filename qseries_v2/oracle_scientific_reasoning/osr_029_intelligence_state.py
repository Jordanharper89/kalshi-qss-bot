from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .osr_028_cross_capability_synthesis import CrossCapabilitySynthesis

OSR_029_BUILD_ID = "OSR-029"
OSR_029_REVISION = "OSR_029_ORACLE_SCIENTIFIC_INTELLIGENCE_STATE_V1"

@dataclass(frozen=True)
class OracleScientificIntelligenceState:
    subject_id: str
    reasoning_state: str
    support: float
    confidence: float
    contradiction: float
    abstain: bool
    lineage: tuple[str, ...]
    synthesis_hash: str
    state_hash: str
    read_only: bool = True
    execution_allowed: bool = False
    publication_allowed: bool = False

def build_oracle_scientific_intelligence_state(subject_id, synthesis):
    if not subject_id or not isinstance(synthesis, CrossCapabilitySynthesis):
        raise ValueError("subject and certified synthesis required")

    raw = {
        "subject_id": subject_id,
        "reasoning_state": synthesis.state,
        "support": synthesis.support,
        "confidence": synthesis.confidence,
        "contradiction": synthesis.contradiction,
        "abstain": synthesis.abstain,
        "lineage": synthesis.participating_capabilities,
        "synthesis_hash": synthesis.synthesis_hash,
        "read_only": True,
        "execution_allowed": False,
        "publication_allowed": False,
    }
    digest = sha256(
        json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    return OracleScientificIntelligenceState(
        subject_id,
        synthesis.state,
        synthesis.support,
        synthesis.confidence,
        synthesis.contradiction,
        synthesis.abstain,
        synthesis.participating_capabilities,
        synthesis.synthesis_hash,
        digest,
    )

def verify_oracle_scientific_intelligence_state(x):
    raw = {
        "subject_id": x.subject_id,
        "reasoning_state": x.reasoning_state,
        "support": x.support,
        "confidence": x.confidence,
        "contradiction": x.contradiction,
        "abstain": x.abstain,
        "lineage": x.lineage,
        "synthesis_hash": x.synthesis_hash,
        "read_only": True,
        "execution_allowed": False,
        "publication_allowed": False,
    }
    digest = sha256(
        json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return (
        x.read_only
        and not x.execution_allowed
        and not x.publication_allowed
        and x.state_hash == digest
    )

def build_osr_029_certification_manifest():
    return MappingProxyType({
        "build_id": OSR_029_BUILD_ID,
        "revision": OSR_029_REVISION,
        "state": "canonical_read_only_scientific_intelligence",
        "execution": False,
        "publication": False,
    })

def verify_osr_029_oracle_scientific_intelligence_state():
    from .osr_028_cross_capability_synthesis import CapabilityReasoningState, synthesize_capabilities
    synthesis = synthesize_capabilities(
        (CapabilityReasoningState("scientific", 0.9, 0.9, 0.1, False),)
    )
    state = build_oracle_scientific_intelligence_state("subject", synthesis)
    return verify_oracle_scientific_intelligence_state(state)
