from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_037_reasoning_evidence_registry import ReasoningEvidenceRegistry

BUILD_ID = "OI-038"
OI_038_REVISION = "OI_038_REASONING_EVIDENCE_CONTEXT_PROJECTION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = False


class ReasoningEvidenceContextProjectionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ReasoningEvidenceContext:
    canonical_observation_id: str
    canonical_observation_hash: str
    adapter_id: str
    provider: str
    subject: str
    observation_type: str
    context_roles: tuple[str, ...]
    context_hash: str


@dataclass(frozen=True, slots=True)
class ReasoningEvidenceContextProjection:
    package_hash: str
    registry_hash: str
    contexts: tuple[ReasoningEvidenceContext, ...]
    context_count: int
    projection_hash: str
    read_only: bool


class ReasoningEvidenceContextProjector:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False
    causal_claim_allowed = False

    @staticmethod
    def _roles_for(
        *,
        provider: str,
        observation_type: str,
    ) -> tuple[str, ...]:
        roles = {"evidence"}

        normalized_type = " ".join(
            str(observation_type).strip().lower().split()
        )
        normalized_provider = " ".join(
            str(provider).strip().lower().split()
        )

        if normalized_type in {
            "market_snapshot",
            "spot_price",
            "orderbook",
        }:
            roles.add("market_state")

        if normalized_type in {
            "news",
            "headline",
            "filing",
            "announcement",
        }:
            roles.add("event_context")

        if normalized_type in {
            "weather",
            "forecast",
            "observation",
        }:
            roles.add("environment_context")

        if normalized_type in {
            "injury",
            "lineup",
            "roster",
            "stat",
        }:
            roles.add("sports_context")

        if normalized_provider:
            roles.add("source_context")

        return tuple(sorted(roles))

    def project(
        self,
        registry: ReasoningEvidenceRegistry,
    ) -> ReasoningEvidenceContextProjection:
        if not isinstance(
            registry,
            ReasoningEvidenceRegistry,
        ):
            raise TypeError(
                "registry must be ReasoningEvidenceRegistry"
            )

        contexts = []

        for record in registry.records:
            roles = self._roles_for(
                provider=record.provider,
                observation_type=record.observation_type,
            )

            body = {
                "canonical_observation_id": (
                    record.canonical_observation_id
                ),
                "canonical_observation_hash": (
                    record.canonical_observation_hash
                ),
                "adapter_id": record.adapter_id,
                "provider": record.provider,
                "subject": record.subject,
                "observation_type": record.observation_type,
                "context_roles": roles,
            }

            contexts.append(
                ReasoningEvidenceContext(
                    canonical_observation_id=(
                        record.canonical_observation_id
                    ),
                    canonical_observation_hash=(
                        record.canonical_observation_hash
                    ),
                    adapter_id=record.adapter_id,
                    provider=record.provider,
                    subject=record.subject,
                    observation_type=record.observation_type,
                    context_roles=roles,
                    context_hash=deterministic_sha256(body),
                )
            )

        ordered = tuple(
            sorted(
                contexts,
                key=lambda item: item.canonical_observation_id,
            )
        )

        body = {
            "package_hash": registry.package_hash,
            "registry_hash": registry.registry_hash,
            "context_hashes": tuple(
                item.context_hash
                for item in ordered
            ),
            "context_count": len(ordered),
            "read_only": True,
        }

        return ReasoningEvidenceContextProjection(
            package_hash=registry.package_hash,
            registry_hash=registry.registry_hash,
            contexts=ordered,
            context_count=len(ordered),
            projection_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_reasoning_evidence_context_projection() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-038 must remain read-only"
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
            CAUSAL_CLAIM_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-038 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_038_REVISION",
    "ReasoningEvidenceContextProjectionError",
    "ReasoningEvidenceContext",
    "ReasoningEvidenceContextProjection",
    "ReasoningEvidenceContextProjector",
    "verify_reasoning_evidence_context_projection",
]
