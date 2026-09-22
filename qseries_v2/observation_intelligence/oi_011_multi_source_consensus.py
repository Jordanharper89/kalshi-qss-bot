from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import median

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_003_canonical_observation_gateway import CanonicalLiveObservation
from .oi_010_observation_freshness_health import (
    FRESH,
    ObservationHealth,
    verify_observation_freshness_health,
)

BUILD_ID = "OI-011"
OI_011_REVISION = "OI_011_MULTI_SOURCE_CONSENSUS_FOUNDATION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False


class MultiSourceConsensusError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SourceConsensusMember:
    canonical_observation_id: str
    source_id: str
    provider: str
    adapter_id: str
    observed_at: datetime
    value: float
    freshness_status: str


@dataclass(frozen=True, slots=True)
class MultiSourceConsensus:
    subject: str
    observation_type: str
    members: tuple[SourceConsensusMember, ...]
    fresh_member_count: int
    source_count: int
    median_value: float
    min_value: float
    max_value: float
    spread_ratio: float
    consensus_hash: str


class MultiSourceConsensusEngine:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def build_numeric_consensus(
        self,
        *,
        observations: tuple[CanonicalLiveObservation, ...],
        health: tuple[ObservationHealth, ...],
        value_field: str,
    ) -> MultiSourceConsensus:
        values = tuple(observations)
        health_values = tuple(health)

        if not values:
            raise MultiSourceConsensusError(
                "at least one observation is required"
            )

        if len(values) != len(health_values):
            raise MultiSourceConsensusError(
                "observation and health counts must match"
            )

        ordered = tuple(
            sorted(
                values,
                key=lambda item: (
                    item.source_id,
                    item.canonical_observation_id,
                ),
            )
        )

        if values != ordered:
            raise MultiSourceConsensusError(
                "observations must be deterministically sorted by source"
            )

        health_by_id = {
            item.canonical_observation_id: item
            for item in health_values
        }

        if len(health_by_id) != len(health_values):
            raise MultiSourceConsensusError(
                "duplicate health observation identity"
            )

        subjects = {item.subject for item in values}
        types = {item.observation_type for item in values}

        if len(subjects) != 1 or len(types) != 1:
            raise MultiSourceConsensusError(
                "consensus observations must share subject and observation_type"
            )

        members = []

        for item in values:
            health_item = health_by_id.get(
                item.canonical_observation_id
            )

            if health_item is None:
                raise MultiSourceConsensusError(
                    "missing health record for observation"
                )

            raw = item.facts.get(value_field)

            try:
                numeric = float(raw)
            except (TypeError, ValueError) as exc:
                raise MultiSourceConsensusError(
                    f"non-numeric consensus field: {value_field}"
                ) from exc

            members.append(
                SourceConsensusMember(
                    canonical_observation_id=item.canonical_observation_id,
                    source_id=item.source_id,
                    provider=item.provider,
                    adapter_id=item.adapter_id,
                    observed_at=item.observed_at,
                    value=numeric,
                    freshness_status=health_item.freshness_status,
                )
            )

        numeric_values = tuple(item.value for item in members)
        middle = float(median(numeric_values))
        low = min(numeric_values)
        high = max(numeric_values)
        spread_ratio = 0.0 if middle == 0 else (high - low) / abs(middle)

        body = {
            "subject": values[0].subject,
            "observation_type": values[0].observation_type,
            "member_ids": tuple(
                item.canonical_observation_id
                for item in members
            ),
            "values": numeric_values,
            "freshness": tuple(
                item.freshness_status
                for item in members
            ),
            "median_value": middle,
            "min_value": low,
            "max_value": high,
            "spread_ratio": spread_ratio,
        }

        return MultiSourceConsensus(
            subject=values[0].subject,
            observation_type=values[0].observation_type,
            members=tuple(members),
            fresh_member_count=sum(
                1
                for item in members
                if item.freshness_status == FRESH
            ),
            source_count=len(
                {item.source_id for item in members}
            ),
            median_value=middle,
            min_value=low,
            max_value=high,
            spread_ratio=spread_ratio,
            consensus_hash=deterministic_sha256(body),
        )


def verify_multi_source_consensus() -> bool:
    verify_observation_freshness_health()

    if READ_ONLY is not True:
        raise AssertionError("OI-011 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-011 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_011_REVISION",
    "MultiSourceConsensusError",
    "SourceConsensusMember",
    "MultiSourceConsensus",
    "MultiSourceConsensusEngine",
    "verify_multi_source_consensus",
]
