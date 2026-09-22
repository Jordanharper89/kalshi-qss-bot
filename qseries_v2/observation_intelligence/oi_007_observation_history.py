from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_003_canonical_observation_gateway import CanonicalLiveObservation
from .oi_006_live_observation_registry import verify_live_observation_registry

BUILD_ID = "OI-007"
OI_007_REVISION = "OI_007_UNIVERSAL_OBSERVATION_HISTORY_FOUNDATION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False


class ObservationHistoryError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ObservationHistorySeries:
    history_key: str
    observations: tuple[CanonicalLiveObservation, ...]
    history_hash: str

    def latest(self) -> CanonicalLiveObservation | None:
        return self.observations[-1] if self.observations else None

    def between(
        self,
        start_at: datetime,
        end_at: datetime,
    ) -> tuple[CanonicalLiveObservation, ...]:
        if not isinstance(start_at, datetime) or not isinstance(end_at, datetime):
            raise TypeError("start_at and end_at must be datetime")
        if start_at.tzinfo is None or end_at.tzinfo is None:
            raise ObservationHistoryError("history query timestamps must be timezone-aware")
        if end_at < start_at:
            raise ObservationHistoryError("end_at must not be before start_at")

        return tuple(
            item
            for item in self.observations
            if start_at <= item.observed_at <= end_at
        )


class UniversalObservationHistory:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def __init__(
        self,
        observations: tuple[CanonicalLiveObservation, ...] = (),
    ) -> None:
        values = tuple(observations)

        if any(not isinstance(item, CanonicalLiveObservation) for item in values):
            raise TypeError("all observations must be CanonicalLiveObservation")

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
            raise ObservationHistoryError(
                "observations must be deterministically sorted"
            )

        ids = tuple(item.canonical_observation_id for item in values)
        if len(ids) != len(set(ids)):
            raise ObservationHistoryError(
                "duplicate canonical observation id"
            )

        grouped: dict[str, list[CanonicalLiveObservation]] = {}

        for item in values:
            key = self.history_key(
                source_id=item.source_id,
                subject=item.subject,
                observation_type=item.observation_type,
            )
            grouped.setdefault(key, []).append(item)

        frozen = {
            key: tuple(items)
            for key, items in sorted(grouped.items())
        }

        self._observations = values
        self._series = MappingProxyType(frozen)

    @staticmethod
    def history_key(
        *,
        source_id: str,
        subject: str,
        observation_type: str,
    ) -> str:
        return "|".join(
            (
                str(source_id).strip().lower(),
                str(subject).strip().upper(),
                str(observation_type).strip().lower(),
            )
        )

    @property
    def observations(self) -> tuple[CanonicalLiveObservation, ...]:
        return self._observations

    @property
    def history_hash(self) -> str:
        return deterministic_sha256(
            tuple(
                item.canonical_observation_hash
                for item in self._observations
            )
        )

    def series(
        self,
        *,
        source_id: str,
        subject: str,
        observation_type: str,
    ) -> ObservationHistorySeries:
        key = self.history_key(
            source_id=source_id,
            subject=subject,
            observation_type=observation_type,
        )
        values = self._series.get(key, ())
        return ObservationHistorySeries(
            history_key=key,
            observations=values,
            history_hash=deterministic_sha256(
                {
                    "history_key": key,
                    "observation_hashes": tuple(
                        item.canonical_observation_hash
                        for item in values
                    ),
                }
            ),
        )

    def latest(
        self,
        *,
        source_id: str,
        subject: str,
        observation_type: str,
    ) -> CanonicalLiveObservation | None:
        return self.series(
            source_id=source_id,
            subject=subject,
            observation_type=observation_type,
        ).latest()


def verify_observation_history() -> bool:
    verify_live_observation_registry()

    if READ_ONLY is not True:
        raise AssertionError("OI-007 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-007 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_007_REVISION",
    "ObservationHistoryError",
    "ObservationHistorySeries",
    "UniversalObservationHistory",
    "verify_observation_history",
]
