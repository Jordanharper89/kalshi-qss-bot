from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_010_observation_freshness_health import (
    ObservationFreshnessHealthEngine,
    ObservationHealth,
    default_freshness_policies,
)
from .oi_012_routed_observation_acquisition import (
    RoutedObservationAcquisitionEngine,
    RoutedObservationAcquisitionResult,
)
from .oi_013_observation_requirement_resolution import (
    ObservationRequirementResolver,
)

BUILD_ID = "OI-014"
OI_014_REVISION = "OI_014_ROUTED_EVIDENCE_ORCHESTRATOR_V1"

READ_ONLY = True
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False


class RoutedEvidenceOrchestratorError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RoutedEvidenceRequirementResult:
    requirement_index: int
    acquisition: RoutedObservationAcquisitionResult
    health: tuple[ObservationHealth, ...]


@dataclass(frozen=True, slots=True)
class RoutedEvidenceOrchestration:
    profile_id: str
    query_id: str
    required_count: int
    satisfied_count: int
    missing_count: int
    results: tuple[RoutedEvidenceRequirementResult, ...]
    orchestration_hash: str


class RoutedEvidenceOrchestrator:
    read_only = True
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def __init__(
        self,
        *,
        requirement_resolver: ObservationRequirementResolver,
        acquisition_engine: RoutedObservationAcquisitionEngine,
        freshness_engine: ObservationFreshnessHealthEngine | None = None,
    ) -> None:
        if not isinstance(
            requirement_resolver,
            ObservationRequirementResolver,
        ):
            raise TypeError(
                "requirement_resolver must be ObservationRequirementResolver"
            )

        if not isinstance(
            acquisition_engine,
            RoutedObservationAcquisitionEngine,
        ):
            raise TypeError(
                "acquisition_engine must be RoutedObservationAcquisitionEngine"
            )

        self._resolver = requirement_resolver
        self._acquisition = acquisition_engine
        self._freshness = (
            freshness_engine
            or ObservationFreshnessHealthEngine(
                default_freshness_policies()
            )
        )

    def orchestrate(
        self,
        *,
        profile_id: str,
        query_id: str,
        evaluated_at: datetime,
    ) -> RoutedEvidenceOrchestration:
        if not isinstance(evaluated_at, datetime):
            raise TypeError("evaluated_at must be datetime")

        if evaluated_at.tzinfo is None:
            raise RoutedEvidenceOrchestratorError(
                "evaluated_at must be timezone-aware"
            )

        evaluated_at = evaluated_at.astimezone(timezone.utc)

        requests = self._resolver.required_requests(
            profile_id
        )

        results = []

        for index, request in enumerate(requests):
            acquisition = self._acquisition.acquire(
                query_id=f"{query_id}.requirement.{index}",
                request=request,
                assembled_at=evaluated_at,
            )

            health = tuple(
                self._freshness.evaluate(
                    observation,
                    evaluated_at=evaluated_at,
                )
                for observation in acquisition.observations
            )

            results.append(
                RoutedEvidenceRequirementResult(
                    requirement_index=index,
                    acquisition=acquisition,
                    health=health,
                )
            )

        satisfied_count = sum(
            1
            for item in results
            if item.acquisition.observations
        )

        required_count = len(results)
        missing_count = required_count - satisfied_count

        body = {
            "profile_id": str(profile_id).strip().lower(),
            "query_id": str(query_id).strip(),
            "required_count": required_count,
            "satisfied_count": satisfied_count,
            "missing_count": missing_count,
            "acquisition_hashes": tuple(
                item.acquisition.acquisition_hash
                for item in results
            ),
            "health_hashes": tuple(
                tuple(health.health_hash for health in item.health)
                for item in results
            ),
        }

        return RoutedEvidenceOrchestration(
            profile_id=str(profile_id).strip().lower(),
            query_id=str(query_id).strip(),
            required_count=required_count,
            satisfied_count=satisfied_count,
            missing_count=missing_count,
            results=tuple(results),
            orchestration_hash=deterministic_sha256(body),
        )


def verify_routed_evidence_orchestrator() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-014 must remain read-only")

    if any(
        (
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-014 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_014_REVISION",
    "RoutedEvidenceOrchestratorError",
    "RoutedEvidenceRequirementResult",
    "RoutedEvidenceOrchestration",
    "RoutedEvidenceOrchestrator",
    "verify_routed_evidence_orchestrator",
]
