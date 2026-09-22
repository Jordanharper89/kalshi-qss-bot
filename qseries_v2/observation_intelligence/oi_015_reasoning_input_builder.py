from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_014_routed_evidence_orchestrator import (
    RoutedEvidenceOrchestration,
)

BUILD_ID = "OI-015"
OI_015_REVISION = "OI_015_REASONING_INPUT_BUILDER_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False


class ReasoningInputBuilderError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ReasoningEvidenceItem:
    canonical_observation_id: str
    canonical_observation_hash: str
    provider: str
    adapter_id: str
    observed_at: datetime
    freshness_status: str
    subject: str
    observation_type: str
    facts: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "facts",
            MappingProxyType(dict(self.facts)),
        )


@dataclass(frozen=True, slots=True)
class OracleReasoningInput:
    query_id: str
    profile_id: str
    built_at: datetime
    evidence_items: tuple[ReasoningEvidenceItem, ...]
    required_evidence_count: int
    satisfied_evidence_count: int
    missing_evidence_count: int
    complete_required_evidence: bool
    input_hash: str
    predictive: bool
    read_only: bool


class OracleReasoningInputBuilder:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False

    def build(
        self,
        orchestration: RoutedEvidenceOrchestration,
        *,
        built_at: datetime,
    ) -> OracleReasoningInput:
        if not isinstance(
            orchestration,
            RoutedEvidenceOrchestration,
        ):
            raise TypeError(
                "orchestration must be RoutedEvidenceOrchestration"
            )

        if not isinstance(built_at, datetime):
            raise TypeError("built_at must be datetime")

        if built_at.tzinfo is None:
            raise ReasoningInputBuilderError(
                "built_at must be timezone-aware"
            )

        built_at = built_at.astimezone(timezone.utc)

        evidence_items = []

        for requirement in orchestration.results:
            health_by_id = {
                item.canonical_observation_id: item
                for item in requirement.health
            }

            for observation in requirement.acquisition.observations:
                health = health_by_id.get(
                    observation.canonical_observation_id
                )

                if health is None:
                    raise ReasoningInputBuilderError(
                        "observation missing freshness health"
                    )

                evidence_items.append(
                    ReasoningEvidenceItem(
                        canonical_observation_id=(
                            observation.canonical_observation_id
                        ),
                        canonical_observation_hash=(
                            observation.canonical_observation_hash
                        ),
                        provider=observation.provider,
                        adapter_id=observation.adapter_id,
                        observed_at=observation.observed_at,
                        freshness_status=health.freshness_status,
                        subject=observation.subject,
                        observation_type=observation.observation_type,
                        facts=dict(observation.facts),
                    )
                )

        ordered = tuple(
            sorted(
                evidence_items,
                key=lambda item: (
                    item.observed_at,
                    item.canonical_observation_id,
                ),
            )
        )

        complete = orchestration.missing_count == 0

        body = {
            "query_id": orchestration.query_id,
            "profile_id": orchestration.profile_id,
            "built_at": built_at,
            "evidence_hashes": tuple(
                item.canonical_observation_hash
                for item in ordered
            ),
            "freshness": tuple(
                item.freshness_status
                for item in ordered
            ),
            "required_evidence_count": orchestration.required_count,
            "satisfied_evidence_count": orchestration.satisfied_count,
            "missing_evidence_count": orchestration.missing_count,
            "complete_required_evidence": complete,
            "predictive": False,
            "read_only": True,
        }

        return OracleReasoningInput(
            query_id=orchestration.query_id,
            profile_id=orchestration.profile_id,
            built_at=built_at,
            evidence_items=ordered,
            required_evidence_count=orchestration.required_count,
            satisfied_evidence_count=orchestration.satisfied_count,
            missing_evidence_count=orchestration.missing_count,
            complete_required_evidence=complete,
            input_hash=deterministic_sha256(body),
            predictive=False,
            read_only=True,
        )


def verify_reasoning_input_builder() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-015 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            PREDICTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-015 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_015_REVISION",
    "ReasoningInputBuilderError",
    "ReasoningEvidenceItem",
    "OracleReasoningInput",
    "OracleReasoningInputBuilder",
    "verify_reasoning_input_builder",
]
