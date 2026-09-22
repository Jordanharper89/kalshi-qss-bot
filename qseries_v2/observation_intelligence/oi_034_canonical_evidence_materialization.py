from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_003_canonical_observation_gateway import CanonicalLiveObservation
from .oi_033_oracle_evidence_intake_package import OracleEvidenceIntakePackage

BUILD_ID = "OI-034"
OI_034_REVISION = "OI_034_CANONICAL_EVIDENCE_MATERIALIZATION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False


class CanonicalEvidenceMaterializationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class MaterializedEvidenceItem:
    canonical_observation_id: str
    canonical_observation_hash: str
    adapter_id: str
    provider: str
    subject: str
    observation_type: str
    observed_at: datetime
    materialization_hash: str


@dataclass(frozen=True, slots=True)
class CanonicalEvidenceMaterialization:
    intake_id: str
    intake_hash: str
    query_id: str
    profile_id: str
    subject_hint: str
    items: tuple[MaterializedEvidenceItem, ...]
    observation_count: int
    complete_count_match: bool
    materialization_hash: str
    read_only: bool


class CanonicalEvidenceMaterializer:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def materialize(
        self,
        *,
        intake: OracleEvidenceIntakePackage,
        observations: tuple[CanonicalLiveObservation, ...],
    ) -> CanonicalEvidenceMaterialization:
        if not isinstance(intake, OracleEvidenceIntakePackage):
            raise TypeError(
                "intake must be OracleEvidenceIntakePackage"
            )

        values = tuple(observations)

        if any(
            not isinstance(item, CanonicalLiveObservation)
            for item in values
        ):
            raise TypeError(
                "all observations must be CanonicalLiveObservation"
            )

        ordered = tuple(
            sorted(
                values,
                key=lambda item: (
                    item.observed_at,
                    item.canonical_observation_id,
                ),
            )
        )

        if values != ordered:
            raise CanonicalEvidenceMaterializationError(
                "observations must be deterministically sorted"
            )

        ids = tuple(
            item.canonical_observation_id
            for item in values
        )

        if len(ids) != len(set(ids)):
            raise CanonicalEvidenceMaterializationError(
                "duplicate canonical observation identity"
            )

        allowed_adapters = {
            adapter_id
            for item in intake.evidence_items
            for adapter_id in item.adapter_ids
        }

        for observation in values:
            if observation.adapter_id not in allowed_adapters:
                raise CanonicalEvidenceMaterializationError(
                    "observation adapter not admitted by intake package"
                )

        items = []

        for observation in values:
            body = {
                "canonical_observation_id": (
                    observation.canonical_observation_id
                ),
                "canonical_observation_hash": (
                    observation.canonical_observation_hash
                ),
                "adapter_id": observation.adapter_id,
                "provider": observation.provider,
                "subject": observation.subject,
                "observation_type": observation.observation_type,
                "observed_at": observation.observed_at,
            }

            items.append(
                MaterializedEvidenceItem(
                    canonical_observation_id=(
                        observation.canonical_observation_id
                    ),
                    canonical_observation_hash=(
                        observation.canonical_observation_hash
                    ),
                    adapter_id=observation.adapter_id,
                    provider=observation.provider,
                    subject=observation.subject,
                    observation_type=observation.observation_type,
                    observed_at=observation.observed_at,
                    materialization_hash=deterministic_sha256(body),
                )
            )

        count_match = (
            len(items)
            == intake.total_observation_count
        )

        body = {
            "intake_id": intake.intake_id,
            "intake_hash": intake.intake_hash,
            "query_id": intake.query_id,
            "profile_id": intake.profile_id,
            "subject_hint": intake.subject_hint,
            "item_hashes": tuple(
                item.materialization_hash
                for item in items
            ),
            "observation_count": len(items),
            "complete_count_match": count_match,
            "read_only": True,
        }

        return CanonicalEvidenceMaterialization(
            intake_id=intake.intake_id,
            intake_hash=intake.intake_hash,
            query_id=intake.query_id,
            profile_id=intake.profile_id,
            subject_hint=intake.subject_hint,
            items=tuple(items),
            observation_count=len(items),
            complete_count_match=count_match,
            materialization_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_canonical_evidence_materialization() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-034 must remain read-only")

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
            "OI-034 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_034_REVISION",
    "CanonicalEvidenceMaterializationError",
    "MaterializedEvidenceItem",
    "CanonicalEvidenceMaterialization",
    "CanonicalEvidenceMaterializer",
    "verify_canonical_evidence_materialization",
]
