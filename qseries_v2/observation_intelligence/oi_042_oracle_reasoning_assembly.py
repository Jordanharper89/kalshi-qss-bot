from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_036_oracle_reasoning_evidence_package import (
    OracleReasoningEvidencePackage,
)
from .oi_039_reasoning_evidence_context_registry import (
    ReasoningEvidenceContextRegistry,
)
from .oi_041_reasoning_evidence_relationship_registry import (
    ReasoningEvidenceRelationshipRegistry,
)

BUILD_ID = "OI-042"
OI_042_REVISION = "OI_042_ORACLE_REASONING_ASSEMBLY_V1"

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


class OracleReasoningAssemblyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OracleReasoningAssembly:
    assembly_id: str
    query_id: str
    profile_id: str
    subject_hint: str
    admission_status: str
    evidence_package_hash: str
    context_registry_hash: str
    relationship_registry_hash: str
    evidence_count: int
    context_count: int
    relationship_count: int
    missing_need_count: int
    assembled_at: datetime
    assembly_hash: str
    read_only: bool
    predictive: bool
    causal_claim_allowed: bool


class OracleReasoningAssembler:
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

    def assemble(
        self,
        *,
        assembly_id: str,
        evidence_package: OracleReasoningEvidencePackage,
        context_registry: ReasoningEvidenceContextRegistry,
        relationship_registry: ReasoningEvidenceRelationshipRegistry,
        assembled_at: datetime,
    ) -> OracleReasoningAssembly:
        assembly_id_value = str(
            assembly_id
        ).strip()

        if not assembly_id_value:
            raise OracleReasoningAssemblyError(
                "assembly_id must not be empty"
            )

        if not isinstance(
            evidence_package,
            OracleReasoningEvidencePackage,
        ):
            raise TypeError(
                "evidence_package must be OracleReasoningEvidencePackage"
            )

        if not isinstance(
            context_registry,
            ReasoningEvidenceContextRegistry,
        ):
            raise TypeError(
                "context_registry must be ReasoningEvidenceContextRegistry"
            )

        if not isinstance(
            relationship_registry,
            ReasoningEvidenceRelationshipRegistry,
        ):
            raise TypeError(
                "relationship_registry must be ReasoningEvidenceRelationshipRegistry"
            )

        if (
            context_registry.package_hash
            != evidence_package.package_hash
        ):
            raise OracleReasoningAssemblyError(
                "context registry does not belong to evidence package"
            )

        if not isinstance(
            assembled_at,
            datetime,
        ):
            raise TypeError(
                "assembled_at must be datetime"
            )

        if assembled_at.tzinfo is None:
            raise OracleReasoningAssemblyError(
                "assembled_at must be timezone-aware"
            )

        assembled_at = assembled_at.astimezone(
            timezone.utc
        )

        body = {
            "assembly_id": assembly_id_value,
            "query_id": evidence_package.query_id,
            "profile_id": evidence_package.profile_id,
            "subject_hint": evidence_package.subject_hint,
            "admission_status": (
                evidence_package.admission_status
            ),
            "evidence_package_hash": (
                evidence_package.package_hash
            ),
            "context_registry_hash": (
                context_registry.registry_hash
            ),
            "relationship_registry_hash": (
                relationship_registry.registry_hash
            ),
            "evidence_count": len(
                evidence_package.evidence_items
            ),
            "context_count": len(
                context_registry.contexts
            ),
            "relationship_count": len(
                relationship_registry.relationships
            ),
            "missing_need_count": (
                evidence_package.missing_need_count
            ),
            "assembled_at": assembled_at,
            "read_only": True,
            "predictive": False,
            "causal_claim_allowed": False,
        }

        return OracleReasoningAssembly(
            assembly_id=assembly_id_value,
            query_id=evidence_package.query_id,
            profile_id=evidence_package.profile_id,
            subject_hint=evidence_package.subject_hint,
            admission_status=(
                evidence_package.admission_status
            ),
            evidence_package_hash=(
                evidence_package.package_hash
            ),
            context_registry_hash=(
                context_registry.registry_hash
            ),
            relationship_registry_hash=(
                relationship_registry.registry_hash
            ),
            evidence_count=len(
                evidence_package.evidence_items
            ),
            context_count=len(
                context_registry.contexts
            ),
            relationship_count=len(
                relationship_registry.relationships
            ),
            missing_need_count=(
                evidence_package.missing_need_count
            ),
            assembled_at=assembled_at,
            assembly_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
            causal_claim_allowed=False,
        )


def verify_oracle_reasoning_assembly() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-042 must remain read-only"
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
            "OI-042 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_042_REVISION",
    "OracleReasoningAssemblyError",
    "OracleReasoningAssembly",
    "OracleReasoningAssembler",
    "verify_oracle_reasoning_assembly",
]
