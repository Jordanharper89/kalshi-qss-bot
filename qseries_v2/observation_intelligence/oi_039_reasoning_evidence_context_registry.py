from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_038_reasoning_evidence_context_projection import (
    ReasoningEvidenceContext,
    ReasoningEvidenceContextProjection,
)

BUILD_ID = "OI-039"
OI_039_REVISION = "OI_039_REASONING_EVIDENCE_CONTEXT_REGISTRY_V1"

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


class ReasoningEvidenceContextRegistryError(ValueError):
    pass


class ReasoningEvidenceContextRegistry:
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

    def __init__(
        self,
        projection: ReasoningEvidenceContextProjection,
    ) -> None:
        if not isinstance(
            projection,
            ReasoningEvidenceContextProjection,
        ):
            raise TypeError(
                "projection must be ReasoningEvidenceContextProjection"
            )

        ids = tuple(
            item.canonical_observation_id
            for item in projection.contexts
        )

        if len(ids) != len(set(ids)):
            raise ReasoningEvidenceContextRegistryError(
                "duplicate canonical observation identity"
            )

        self._projection = projection
        self._contexts = tuple(projection.contexts)

        self._by_id = MappingProxyType(
            {
                item.canonical_observation_id: item
                for item in self._contexts
            }
        )

    @property
    def contexts(self) -> tuple[ReasoningEvidenceContext, ...]:
        return self._contexts

    @property
    def package_hash(self) -> str:
        return self._projection.package_hash

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(
            {
                "package_hash": self._projection.package_hash,
                "projection_hash": self._projection.projection_hash,
                "context_hashes": tuple(
                    item.context_hash
                    for item in self._contexts
                ),
            }
        )

    def get(
        self,
        canonical_observation_id: str,
    ) -> ReasoningEvidenceContext | None:
        return self._by_id.get(
            str(canonical_observation_id).strip()
        )

    def by_role(
        self,
        role: str,
    ) -> tuple[ReasoningEvidenceContext, ...]:
        key = " ".join(
            str(role).strip().lower().split()
        )

        return tuple(
            item
            for item in self._contexts
            if key in item.context_roles
        )

    def by_adapter(
        self,
        adapter_id: str,
    ) -> tuple[ReasoningEvidenceContext, ...]:
        key = str(adapter_id).strip()

        return tuple(
            item
            for item in self._contexts
            if item.adapter_id == key
        )

    def by_subject(
        self,
        subject: str,
    ) -> tuple[ReasoningEvidenceContext, ...]:
        key = " ".join(
            str(subject).strip().split()
        )

        return tuple(
            item
            for item in self._contexts
            if item.subject == key
        )


def verify_reasoning_evidence_context_registry() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-039 must remain read-only"
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
            "OI-039 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_039_REVISION",
    "ReasoningEvidenceContextRegistryError",
    "ReasoningEvidenceContextRegistry",
    "verify_reasoning_evidence_context_registry",
]
