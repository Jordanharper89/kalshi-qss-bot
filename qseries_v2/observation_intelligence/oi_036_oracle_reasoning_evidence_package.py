from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_034_canonical_evidence_materialization import (
    CanonicalEvidenceMaterialization,
)
from .oi_035_reasoning_evidence_admission_gate import (
    ReasoningEvidenceAdmission,
    REJECTED,
)

BUILD_ID = "OI-036"
OI_036_REVISION = "OI_036_ORACLE_REASONING_EVIDENCE_PACKAGE_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False


class OracleReasoningEvidencePackageError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OracleReasoningEvidenceItem:
    canonical_observation_id: str
    canonical_observation_hash: str
    adapter_id: str
    provider: str
    subject: str
    observation_type: str
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class OracleReasoningEvidencePackage:
    package_id: str
    query_id: str
    profile_id: str
    subject_hint: str
    admission_status: str
    admission_hash: str
    materialization_hash: str
    evidence_items: tuple[OracleReasoningEvidenceItem, ...]
    missing_need_count: int
    built_at: datetime
    package_hash: str
    read_only: bool
    predictive: bool


class OracleReasoningEvidencePackageBuilder:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def build(
        self,
        *,
        package_id: str,
        materialization: CanonicalEvidenceMaterialization,
        admission: ReasoningEvidenceAdmission,
        built_at: datetime,
    ) -> OracleReasoningEvidencePackage:
        package_id_value = str(package_id).strip()

        if not package_id_value:
            raise OracleReasoningEvidencePackageError(
                "package_id must not be empty"
            )

        if not isinstance(
            materialization,
            CanonicalEvidenceMaterialization,
        ):
            raise TypeError(
                "materialization must be CanonicalEvidenceMaterialization"
            )

        if not isinstance(
            admission,
            ReasoningEvidenceAdmission,
        ):
            raise TypeError(
                "admission must be ReasoningEvidenceAdmission"
            )

        if (
            admission.materialization_hash
            != materialization.materialization_hash
        ):
            raise OracleReasoningEvidencePackageError(
                "admission does not belong to materialization"
            )

        if admission.status == REJECTED:
            raise OracleReasoningEvidencePackageError(
                "rejected evidence cannot enter reasoning package"
            )

        if not isinstance(built_at, datetime):
            raise TypeError(
                "built_at must be datetime"
            )

        if built_at.tzinfo is None:
            raise OracleReasoningEvidencePackageError(
                "built_at must be timezone-aware"
            )

        built_at = built_at.astimezone(
            timezone.utc
        )

        items = tuple(
            OracleReasoningEvidenceItem(
                canonical_observation_id=(
                    item.canonical_observation_id
                ),
                canonical_observation_hash=(
                    item.canonical_observation_hash
                ),
                adapter_id=item.adapter_id,
                provider=item.provider,
                subject=item.subject,
                observation_type=item.observation_type,
                observed_at=item.observed_at,
            )
            for item in materialization.items
        )

        body = {
            "package_id": package_id_value,
            "query_id": materialization.query_id,
            "profile_id": materialization.profile_id,
            "subject_hint": materialization.subject_hint,
            "admission_status": admission.status,
            "admission_hash": admission.admission_hash,
            "materialization_hash": (
                materialization.materialization_hash
            ),
            "evidence": tuple(
                (
                    item.canonical_observation_id,
                    item.canonical_observation_hash,
                    item.adapter_id,
                    item.provider,
                    item.subject,
                    item.observation_type,
                    item.observed_at,
                )
                for item in items
            ),
            "missing_need_count": admission.missing_need_count,
            "built_at": built_at,
            "read_only": True,
            "predictive": False,
        }

        return OracleReasoningEvidencePackage(
            package_id=package_id_value,
            query_id=materialization.query_id,
            profile_id=materialization.profile_id,
            subject_hint=materialization.subject_hint,
            admission_status=admission.status,
            admission_hash=admission.admission_hash,
            materialization_hash=(
                materialization.materialization_hash
            ),
            evidence_items=items,
            missing_need_count=admission.missing_need_count,
            built_at=built_at,
            package_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
        )


def verify_oracle_reasoning_evidence_package() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-036 must remain read-only"
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
            "OI-036 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_036_REVISION",
    "OracleReasoningEvidencePackageError",
    "OracleReasoningEvidenceItem",
    "OracleReasoningEvidencePackage",
    "OracleReasoningEvidencePackageBuilder",
    "verify_oracle_reasoning_evidence_package",
]
