from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_015_reasoning_input_builder import OracleReasoningInput
from .oi_016_evidence_sufficiency_gate import EvidenceSufficiencyDecision
from .oi_017_observation_change_attribution import ObservationChange

BUILD_ID = "OI-018"
OI_018_REVISION = "OI_018_EXPLANATION_EVIDENCE_PACKAGE_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = False
PREDICTION_ALLOWED = False


class ExplanationEvidencePackageError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ExplanationEvidencePackage:
    query_id: str
    profile_id: str
    built_at: datetime
    reasoning_input_hash: str
    sufficiency_decision_hash: str
    sufficient_evidence: bool
    evidence_item_count: int
    change_hashes: tuple[str, ...]
    package_hash: str
    causal_claim_allowed: bool
    predictive: bool
    read_only: bool


class ExplanationEvidencePackageBuilder:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    causal_claim_allowed = False
    prediction_allowed = False

    def build(
        self,
        *,
        reasoning_input: OracleReasoningInput,
        sufficiency: EvidenceSufficiencyDecision,
        changes: tuple[ObservationChange, ...],
        built_at: datetime,
    ) -> ExplanationEvidencePackage:
        if not isinstance(reasoning_input, OracleReasoningInput):
            raise TypeError(
                "reasoning_input must be OracleReasoningInput"
            )
        if not isinstance(sufficiency, EvidenceSufficiencyDecision):
            raise TypeError(
                "sufficiency must be EvidenceSufficiencyDecision"
            )

        values = tuple(changes)

        if any(
            not isinstance(item, ObservationChange)
            for item in values
        ):
            raise TypeError("all changes must be ObservationChange")

        if sufficiency.input_hash != reasoning_input.input_hash:
            raise ExplanationEvidencePackageError(
                "sufficiency decision does not belong to reasoning input"
            )

        if not isinstance(built_at, datetime):
            raise TypeError("built_at must be datetime")

        if built_at.tzinfo is None:
            raise ExplanationEvidencePackageError(
                "built_at must be timezone-aware"
            )

        built_at = built_at.astimezone(timezone.utc)

        ordered_changes = tuple(
            sorted(
                values,
                key=lambda item: (
                    item.subject,
                    item.observation_type,
                    item.value_field,
                    item.prior_observation_id,
                    item.current_observation_id,
                ),
            )
        )

        change_hashes = tuple(
            item.change_hash
            for item in ordered_changes
        )

        body = {
            "query_id": reasoning_input.query_id,
            "profile_id": reasoning_input.profile_id,
            "built_at": built_at,
            "reasoning_input_hash": reasoning_input.input_hash,
            "sufficiency_decision_hash": sufficiency.decision_hash,
            "sufficient_evidence": sufficiency.sufficient,
            "evidence_item_count": len(reasoning_input.evidence_items),
            "change_hashes": change_hashes,
            "causal_claim_allowed": False,
            "predictive": False,
            "read_only": True,
        }

        return ExplanationEvidencePackage(
            query_id=reasoning_input.query_id,
            profile_id=reasoning_input.profile_id,
            built_at=built_at,
            reasoning_input_hash=reasoning_input.input_hash,
            sufficiency_decision_hash=sufficiency.decision_hash,
            sufficient_evidence=sufficiency.sufficient,
            evidence_item_count=len(reasoning_input.evidence_items),
            change_hashes=change_hashes,
            package_hash=deterministic_sha256(body),
            causal_claim_allowed=False,
            predictive=False,
            read_only=True,
        )


def verify_explanation_evidence_package() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-018 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            CAUSAL_CLAIM_ALLOWED,
            PREDICTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-018 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_018_REVISION",
    "ExplanationEvidencePackageError",
    "ExplanationEvidencePackage",
    "ExplanationEvidencePackageBuilder",
    "verify_explanation_evidence_package",
]
