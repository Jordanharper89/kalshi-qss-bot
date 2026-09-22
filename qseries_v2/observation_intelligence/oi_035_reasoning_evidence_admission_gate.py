from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_033_oracle_evidence_intake_package import OracleEvidenceIntakePackage
from .oi_034_canonical_evidence_materialization import (
    CanonicalEvidenceMaterialization,
)

BUILD_ID = "OI-035"
OI_035_REVISION = "OI_035_REASONING_EVIDENCE_ADMISSION_GATE_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False

ADMITTED = "admitted"
PARTIAL = "partial"
REJECTED = "rejected"


class ReasoningEvidenceAdmissionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ReasoningEvidenceAdmission:
    intake_hash: str
    materialization_hash: str
    status: str
    observation_count: int
    missing_need_count: int
    complete_count_match: bool
    reason_codes: tuple[str, ...]
    admission_hash: str
    read_only: bool


class ReasoningEvidenceAdmissionGate:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def evaluate(
        self,
        *,
        intake: OracleEvidenceIntakePackage,
        materialization: CanonicalEvidenceMaterialization,
    ) -> ReasoningEvidenceAdmission:
        if not isinstance(
            intake,
            OracleEvidenceIntakePackage,
        ):
            raise TypeError(
                "intake must be OracleEvidenceIntakePackage"
            )

        if not isinstance(
            materialization,
            CanonicalEvidenceMaterialization,
        ):
            raise TypeError(
                "materialization must be CanonicalEvidenceMaterialization"
            )

        if materialization.intake_hash != intake.intake_hash:
            raise ReasoningEvidenceAdmissionError(
                "materialization does not belong to intake package"
            )

        reasons = []

        if materialization.observation_count < 1:
            reasons.append("no_canonical_observations")

        if not materialization.complete_count_match:
            reasons.append("observation_count_mismatch")

        if intake.missing_need_ids:
            reasons.append("missing_required_observation_needs")

        reasons = tuple(
            sorted(set(reasons))
        )

        if (
            materialization.observation_count < 1
            or not materialization.complete_count_match
        ):
            status = REJECTED
        elif intake.missing_need_ids:
            status = PARTIAL
        else:
            status = ADMITTED

        body = {
            "intake_hash": intake.intake_hash,
            "materialization_hash": (
                materialization.materialization_hash
            ),
            "status": status,
            "observation_count": (
                materialization.observation_count
            ),
            "missing_need_count": len(
                intake.missing_need_ids
            ),
            "complete_count_match": (
                materialization.complete_count_match
            ),
            "reason_codes": reasons,
            "read_only": True,
        }

        return ReasoningEvidenceAdmission(
            intake_hash=intake.intake_hash,
            materialization_hash=(
                materialization.materialization_hash
            ),
            status=status,
            observation_count=(
                materialization.observation_count
            ),
            missing_need_count=len(
                intake.missing_need_ids
            ),
            complete_count_match=(
                materialization.complete_count_match
            ),
            reason_codes=reasons,
            admission_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_reasoning_evidence_admission_gate() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-035 must remain read-only"
        )

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            PREDICTION_ALLOWED,
            EDGE_SCORE_ALLOWED,
            PROBABILITY_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-035 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_035_REVISION",
    "ADMITTED",
    "PARTIAL",
    "REJECTED",
    "ReasoningEvidenceAdmissionError",
    "ReasoningEvidenceAdmission",
    "ReasoningEvidenceAdmissionGate",
    "verify_reasoning_evidence_admission_gate",
]
