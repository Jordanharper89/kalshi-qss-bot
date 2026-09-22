from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Mapping

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_003_canonical_observation_gateway import CanonicalLiveObservation
from .oi_009_observation_evidence_assembly import verify_observation_evidence_assembly

BUILD_ID = "OI-010"
OI_010_REVISION = "OI_010_OBSERVATION_FRESHNESS_HEALTH_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False

FRESH = "fresh"
AGING = "aging"
STALE = "stale"


class ObservationFreshnessHealthError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class FreshnessPolicy:
    observation_type: str
    fresh_seconds: int
    stale_seconds: int

    def __post_init__(self) -> None:
        kind = " ".join(str(self.observation_type).strip().lower().split())
        if not kind:
            raise ObservationFreshnessHealthError(
                "observation_type must not be empty"
            )
        if not isinstance(self.fresh_seconds, int) or self.fresh_seconds < 0:
            raise ObservationFreshnessHealthError(
                "fresh_seconds must be a non-negative integer"
            )
        if not isinstance(self.stale_seconds, int) or self.stale_seconds <= self.fresh_seconds:
            raise ObservationFreshnessHealthError(
                "stale_seconds must be greater than fresh_seconds"
            )

        object.__setattr__(self, "observation_type", kind)

    @property
    def policy_hash(self) -> str:
        return deterministic_sha256(
            {
                "observation_type": self.observation_type,
                "fresh_seconds": self.fresh_seconds,
                "stale_seconds": self.stale_seconds,
            }
        )


@dataclass(frozen=True, slots=True)
class ObservationHealth:
    canonical_observation_id: str
    observed_at: datetime
    evaluated_at: datetime
    age_seconds: int
    freshness_status: str
    policy_hash: str
    health_hash: str


class ObservationFreshnessHealthEngine:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def __init__(
        self,
        policies: tuple[FreshnessPolicy, ...],
    ) -> None:
        values = tuple(policies)

        if any(not isinstance(item, FreshnessPolicy) for item in values):
            raise TypeError("all policies must be FreshnessPolicy")

        ordered = tuple(
            sorted(values, key=lambda item: item.observation_type)
        )

        if values != ordered:
            raise ObservationFreshnessHealthError(
                "policies must be deterministically sorted"
            )

        keys = tuple(item.observation_type for item in values)
        if len(keys) != len(set(keys)):
            raise ObservationFreshnessHealthError(
                "duplicate observation_type policy"
            )

        self._policies = values
        self._by_type = MappingProxyType(
            {item.observation_type: item for item in values}
        )

    @property
    def policies(self) -> tuple[FreshnessPolicy, ...]:
        return self._policies

    def evaluate(
        self,
        observation: CanonicalLiveObservation,
        *,
        evaluated_at: datetime,
    ) -> ObservationHealth:
        if not isinstance(observation, CanonicalLiveObservation):
            raise TypeError(
                "observation must be CanonicalLiveObservation"
            )

        if not isinstance(evaluated_at, datetime):
            raise TypeError("evaluated_at must be datetime")

        if evaluated_at.tzinfo is None:
            raise ObservationFreshnessHealthError(
                "evaluated_at must be timezone-aware"
            )

        evaluated_at = evaluated_at.astimezone(timezone.utc)

        if evaluated_at < observation.observed_at:
            raise ObservationFreshnessHealthError(
                "evaluated_at cannot precede observed_at"
            )

        policy = self._by_type.get(observation.observation_type)

        if policy is None:
            raise ObservationFreshnessHealthError(
                f"no freshness policy for observation type: "
                f"{observation.observation_type}"
            )

        age_seconds = int(
            (evaluated_at - observation.observed_at).total_seconds()
        )

        if age_seconds <= policy.fresh_seconds:
            status = FRESH
        elif age_seconds < policy.stale_seconds:
            status = AGING
        else:
            status = STALE

        body = {
            "canonical_observation_id": observation.canonical_observation_id,
            "observed_at": observation.observed_at,
            "evaluated_at": evaluated_at,
            "age_seconds": age_seconds,
            "freshness_status": status,
            "policy_hash": policy.policy_hash,
        }

        return ObservationHealth(
            canonical_observation_id=observation.canonical_observation_id,
            observed_at=observation.observed_at,
            evaluated_at=evaluated_at,
            age_seconds=age_seconds,
            freshness_status=status,
            policy_hash=policy.policy_hash,
            health_hash=deterministic_sha256(body),
        )


def default_freshness_policies() -> tuple[FreshnessPolicy, ...]:
    return (
        FreshnessPolicy(
            observation_type="market_snapshot",
            fresh_seconds=15,
            stale_seconds=90,
        ),
        FreshnessPolicy(
            observation_type="spot_price",
            fresh_seconds=10,
            stale_seconds=60,
        ),
    )


def verify_observation_freshness_health() -> bool:
    verify_observation_evidence_assembly()

    if READ_ONLY is not True:
        raise AssertionError("OI-010 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-010 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_010_REVISION",
    "FRESH",
    "AGING",
    "STALE",
    "ObservationFreshnessHealthError",
    "FreshnessPolicy",
    "ObservationHealth",
    "ObservationFreshnessHealthEngine",
    "default_freshness_policies",
    "verify_observation_freshness_health",
]
