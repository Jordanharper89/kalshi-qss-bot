from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone

from .oad_122_authoritative_sports_live_end_to_end_evidence_certification import run_live_sports_end_to_end_evidence_certification
from .oad_123_authoritative_sports_market_evidence_envelope import build_sports_market_evidence_envelopes
from .oad_124_authoritative_sports_reasoning_comparison_input import build_sports_reasoning_comparison_inputs
from .oad_125_authoritative_sports_reasoning_readiness_gate import evaluate_sports_reasoning_readiness

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True, slots=True)
class PhysicalSportsReasoningEvidenceGate:
    persisted_observations: int
    current_markets: int
    association_candidates: int
    evidence_envelopes: int
    reasoning_inputs: int
    ready_for_evidence_comparison_markets: int
    ready_for_prediction_markets: int
    state: str
    certified_at: str
    read_only: bool=True
    probability_enabled: bool=False
    execution_authority: bool=False

def run_physical_sports_reasoning_evidence_gate(
    root=None,
    market_limit=1000,
    timeout_seconds=120.0,
    acquisition_timeout_seconds=20.0,
    market_timeout_seconds=20.0,
):
    live=run_live_sports_end_to_end_evidence_certification(
        root=root,
        market_limit=market_limit,
        timeout_seconds=timeout_seconds,
        acquisition_timeout_seconds=acquisition_timeout_seconds,
        market_timeout_seconds=market_timeout_seconds,
    )
    envelopes=build_sports_market_evidence_envelopes(live)
    inputs=build_sports_reasoning_comparison_inputs(envelopes)
    readiness=evaluate_sports_reasoning_readiness(inputs)
    comparison_ready=sum(1 for x in readiness if x.ready_for_evidence_comparison)
    prediction_ready=sum(1 for x in readiness if x.ready_for_prediction)
    if prediction_ready:
        raise RuntimeError("adapter layer may not certify prediction readiness")
    state="READY_FOR_EVIDENCE_COMPARISON" if comparison_ready else "OBSERVE"
    return PhysicalSportsReasoningEvidenceGate(
        persisted_observations=live.persisted_observations,
        current_markets=live.current_markets,
        association_candidates=live.association_candidates,
        evidence_envelopes=len(envelopes),
        reasoning_inputs=len(inputs),
        ready_for_evidence_comparison_markets=comparison_ready,
        ready_for_prediction_markets=0,
        state=state,
        certified_at=datetime.now(timezone.utc).isoformat(),
        read_only=True,
        probability_enabled=False,
        execution_authority=False,
    )
