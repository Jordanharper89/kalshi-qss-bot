from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_015_reasoning_input_builder import OracleReasoningInput

BUILD_ID = "OI-016"
OI_016_REVISION = "OI_016_EVIDENCE_SUFFICIENCY_GATE_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False


class EvidenceSufficiencyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EvidenceSufficiencyPolicy:
    policy_id: str
    minimum_evidence_items: int
    minimum_distinct_sources: int
    allow_stale_evidence: bool

    def __post_init__(self) -> None:
        policy_id = " ".join(
            str(self.policy_id).strip().lower().split()
        )
        if not policy_id:
            raise EvidenceSufficiencyError(
                "policy_id must not be empty"
            )
        if (
            not isinstance(self.minimum_evidence_items, int)
            or self.minimum_evidence_items < 0
        ):
            raise EvidenceSufficiencyError(
                "minimum_evidence_items must be non-negative"
            )
        if (
            not isinstance(self.minimum_distinct_sources, int)
            or self.minimum_distinct_sources < 0
        ):
            raise EvidenceSufficiencyError(
                "minimum_distinct_sources must be non-negative"
            )
        object.__setattr__(self, "policy_id", policy_id)

    @property
    def policy_hash(self) -> str:
        return deterministic_sha256(
            {
                "policy_id": self.policy_id,
                "minimum_evidence_items": self.minimum_evidence_items,
                "minimum_distinct_sources": self.minimum_distinct_sources,
                "allow_stale_evidence": self.allow_stale_evidence,
            }
        )


@dataclass(frozen=True, slots=True)
class EvidenceSufficiencyDecision:
    policy_id: str
    input_hash: str
    evidence_item_count: int
    distinct_source_count: int
    stale_evidence_count: int
    complete_required_evidence: bool
    sufficient: bool
    reason_codes: tuple[str, ...]
    decision_hash: str


class EvidenceSufficiencyGate:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False

    def evaluate(
        self,
        reasoning_input: OracleReasoningInput,
        *,
        policy: EvidenceSufficiencyPolicy,
    ) -> EvidenceSufficiencyDecision:
        if not isinstance(reasoning_input, OracleReasoningInput):
            raise TypeError(
                "reasoning_input must be OracleReasoningInput"
            )
        if not isinstance(policy, EvidenceSufficiencyPolicy):
            raise TypeError(
                "policy must be EvidenceSufficiencyPolicy"
            )

        item_count = len(reasoning_input.evidence_items)
        distinct_sources = len(
            {
                item.adapter_id
                for item in reasoning_input.evidence_items
            }
        )
        stale_count = sum(
            1
            for item in reasoning_input.evidence_items
            if item.freshness_status == "stale"
        )

        reasons = []

        if reasoning_input.complete_required_evidence is not True:
            reasons.append("missing_required_evidence")

        if item_count < policy.minimum_evidence_items:
            reasons.append("insufficient_evidence_items")

        if distinct_sources < policy.minimum_distinct_sources:
            reasons.append("insufficient_source_diversity")

        if stale_count and not policy.allow_stale_evidence:
            reasons.append("stale_evidence_present")

        reasons = tuple(sorted(set(reasons)))
        sufficient = not reasons

        body = {
            "policy_id": policy.policy_id,
            "policy_hash": policy.policy_hash,
            "input_hash": reasoning_input.input_hash,
            "evidence_item_count": item_count,
            "distinct_source_count": distinct_sources,
            "stale_evidence_count": stale_count,
            "complete_required_evidence": (
                reasoning_input.complete_required_evidence
            ),
            "sufficient": sufficient,
            "reason_codes": reasons,
        }

        return EvidenceSufficiencyDecision(
            policy_id=policy.policy_id,
            input_hash=reasoning_input.input_hash,
            evidence_item_count=item_count,
            distinct_source_count=distinct_sources,
            stale_evidence_count=stale_count,
            complete_required_evidence=(
                reasoning_input.complete_required_evidence
            ),
            sufficient=sufficient,
            reason_codes=reasons,
            decision_hash=deterministic_sha256(body),
        )


def verify_evidence_sufficiency_gate() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-016 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            PREDICTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-016 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_016_REVISION",
    "EvidenceSufficiencyError",
    "EvidenceSufficiencyPolicy",
    "EvidenceSufficiencyDecision",
    "EvidenceSufficiencyGate",
    "verify_evidence_sufficiency_gate",
]
