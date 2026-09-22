from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_003_canonical_observation_gateway import CanonicalLiveObservation
from .oi_017_observation_change_attribution import ObservationChange

BUILD_ID = "OI-020"
OI_020_REVISION = "OI_020_TEMPORAL_ASSOCIATION_FOUNDATION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
CAUSAL_INFERENCE_ALLOWED = False
PREDICTION_ALLOWED = False


class TemporalAssociationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TemporalAssociation:
    change_hash: str
    evidence_observation_id: str
    evidence_subject: str
    evidence_observation_type: str
    evidence_observed_at: datetime
    seconds_from_change_observation: int
    temporal_relation: str
    association_hash: str


class TemporalAssociationEngine:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    causal_inference_allowed = False
    prediction_allowed = False

    def associate(
        self,
        *,
        change: ObservationChange,
        change_observed_at: datetime,
        evidence: tuple[CanonicalLiveObservation, ...],
        max_window_seconds: int,
    ) -> tuple[TemporalAssociation, ...]:
        if not isinstance(change, ObservationChange):
            raise TypeError(
                "change must be ObservationChange"
            )

        if not isinstance(change_observed_at, datetime):
            raise TypeError(
                "change_observed_at must be datetime"
            )

        if change_observed_at.tzinfo is None:
            raise TemporalAssociationError(
                "change_observed_at must be timezone-aware"
            )

        if (
            not isinstance(max_window_seconds, int)
            or max_window_seconds < 0
        ):
            raise TemporalAssociationError(
                "max_window_seconds must be a non-negative integer"
            )

        values = tuple(evidence)

        if any(
            not isinstance(item, CanonicalLiveObservation)
            for item in values
        ):
            raise TypeError(
                "all evidence must be CanonicalLiveObservation"
            )

        associations = []

        for item in values:
            delta = int(
                (
                    item.observed_at
                    - change_observed_at
                ).total_seconds()
            )

            if abs(delta) > max_window_seconds:
                continue

            if delta < 0:
                relation = "before"
            elif delta > 0:
                relation = "after"
            else:
                relation = "simultaneous"

            body = {
                "change_hash": change.change_hash,
                "evidence_observation_id": (
                    item.canonical_observation_id
                ),
                "evidence_subject": item.subject,
                "evidence_observation_type": (
                    item.observation_type
                ),
                "evidence_observed_at": item.observed_at,
                "seconds_from_change_observation": delta,
                "temporal_relation": relation,
            }

            associations.append(
                TemporalAssociation(
                    change_hash=change.change_hash,
                    evidence_observation_id=(
                        item.canonical_observation_id
                    ),
                    evidence_subject=item.subject,
                    evidence_observation_type=(
                        item.observation_type
                    ),
                    evidence_observed_at=item.observed_at,
                    seconds_from_change_observation=delta,
                    temporal_relation=relation,
                    association_hash=(
                        deterministic_sha256(body)
                    ),
                )
            )

        return tuple(
            sorted(
                associations,
                key=lambda item: (
                    abs(
                        item.seconds_from_change_observation
                    ),
                    item.evidence_observation_id,
                ),
            )
        )


def verify_temporal_association() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-020 must remain read-only"
        )

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            CAUSAL_INFERENCE_ALLOWED,
            PREDICTION_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-020 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_020_REVISION",
    "TemporalAssociationError",
    "TemporalAssociation",
    "TemporalAssociationEngine",
    "verify_temporal_association",
]
