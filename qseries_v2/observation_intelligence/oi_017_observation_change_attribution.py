from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_003_canonical_observation_gateway import CanonicalLiveObservation

BUILD_ID = "OI-017"
OI_017_REVISION = "OI_017_OBSERVATION_CHANGE_ATTRIBUTION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
CAUSAL_INFERENCE_ALLOWED = False
PREDICTION_ALLOWED = False


class ObservationChangeAttributionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ObservationChange:
    subject: str
    observation_type: str
    value_field: str
    prior_observation_id: str
    current_observation_id: str
    prior_value: float
    current_value: float
    absolute_change: float
    relative_change: float | None
    direction: str
    change_hash: str


class ObservationChangeAttributionEngine:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    causal_inference_allowed = False
    prediction_allowed = False

    def compare_numeric(
        self,
        *,
        prior: CanonicalLiveObservation,
        current: CanonicalLiveObservation,
        value_field: str,
    ) -> ObservationChange:
        if not isinstance(prior, CanonicalLiveObservation):
            raise TypeError("prior must be CanonicalLiveObservation")
        if not isinstance(current, CanonicalLiveObservation):
            raise TypeError("current must be CanonicalLiveObservation")

        if prior.subject != current.subject:
            raise ObservationChangeAttributionError(
                "observations must share subject"
            )

        if prior.observation_type != current.observation_type:
            raise ObservationChangeAttributionError(
                "observations must share observation_type"
            )

        if current.observed_at <= prior.observed_at:
            raise ObservationChangeAttributionError(
                "current observation must be later than prior observation"
            )

        field = str(value_field).strip()
        if not field:
            raise ObservationChangeAttributionError(
                "value_field must not be empty"
            )

        try:
            prior_value = float(prior.facts[field])
            current_value = float(current.facts[field])
        except (KeyError, TypeError, ValueError) as exc:
            raise ObservationChangeAttributionError(
                f"numeric value field unavailable: {field}"
            ) from exc

        absolute_change = current_value - prior_value

        if absolute_change > 0:
            direction = "up"
        elif absolute_change < 0:
            direction = "down"
        else:
            direction = "unchanged"

        relative_change = (
            None
            if prior_value == 0
            else absolute_change / abs(prior_value)
        )

        body = {
            "subject": prior.subject,
            "observation_type": prior.observation_type,
            "value_field": field,
            "prior_observation_id": prior.canonical_observation_id,
            "current_observation_id": current.canonical_observation_id,
            "prior_value": prior_value,
            "current_value": current_value,
            "absolute_change": absolute_change,
            "relative_change": relative_change,
            "direction": direction,
        }

        return ObservationChange(
            subject=prior.subject,
            observation_type=prior.observation_type,
            value_field=field,
            prior_observation_id=prior.canonical_observation_id,
            current_observation_id=current.canonical_observation_id,
            prior_value=prior_value,
            current_value=current_value,
            absolute_change=absolute_change,
            relative_change=relative_change,
            direction=direction,
            change_hash=deterministic_sha256(body),
        )


def verify_observation_change_attribution() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-017 must remain read-only")

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
        raise AssertionError("OI-017 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_017_REVISION",
    "ObservationChangeAttributionError",
    "ObservationChange",
    "ObservationChangeAttributionEngine",
    "verify_observation_change_attribution",
]
