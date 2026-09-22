from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_036_oracle_reasoning_evidence_package import (
    OracleReasoningEvidenceItem,
    OracleReasoningEvidencePackage,
)

BUILD_ID = "OI-037"
OI_037_REVISION = "OI_037_REASONING_EVIDENCE_REGISTRY_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False


class ReasoningEvidenceRegistryError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ReasoningEvidenceRegistryRecord:
    canonical_observation_id: str
    canonical_observation_hash: str
    adapter_id: str
    provider: str
    subject: str
    observation_type: str


class ReasoningEvidenceRegistry:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def __init__(
        self,
        package: OracleReasoningEvidencePackage,
    ) -> None:
        if not isinstance(
            package,
            OracleReasoningEvidencePackage,
        ):
            raise TypeError(
                "package must be OracleReasoningEvidencePackage"
            )

        records = tuple(
            ReasoningEvidenceRegistryRecord(
                canonical_observation_id=item.canonical_observation_id,
                canonical_observation_hash=item.canonical_observation_hash,
                adapter_id=item.adapter_id,
                provider=item.provider,
                subject=item.subject,
                observation_type=item.observation_type,
            )
            for item in package.evidence_items
        )

        ordered = tuple(
            sorted(
                records,
                key=lambda item: item.canonical_observation_id,
            )
        )

        ids = tuple(
            item.canonical_observation_id
            for item in ordered
        )

        if len(ids) != len(set(ids)):
            raise ReasoningEvidenceRegistryError(
                "duplicate canonical observation identity"
            )

        self._package = package
        self._records = ordered
        self._by_id = MappingProxyType(
            {
                item.canonical_observation_id: item
                for item in ordered
            }
        )

    @property
    def package_hash(self) -> str:
        return self._package.package_hash

    @property
    def records(self) -> tuple[ReasoningEvidenceRegistryRecord, ...]:
        return self._records

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(
            {
                "package_hash": self._package.package_hash,
                "record_ids": tuple(
                    item.canonical_observation_id
                    for item in self._records
                ),
                "record_hashes": tuple(
                    item.canonical_observation_hash
                    for item in self._records
                ),
            }
        )

    def get(
        self,
        canonical_observation_id: str,
    ) -> ReasoningEvidenceRegistryRecord | None:
        key = str(canonical_observation_id).strip()
        return self._by_id.get(key)

    def by_adapter(
        self,
        adapter_id: str,
    ) -> tuple[ReasoningEvidenceRegistryRecord, ...]:
        key = str(adapter_id).strip()
        return tuple(
            item
            for item in self._records
            if item.adapter_id == key
        )

    def by_provider(
        self,
        provider: str,
    ) -> tuple[ReasoningEvidenceRegistryRecord, ...]:
        key = " ".join(str(provider).strip().split())
        return tuple(
            item
            for item in self._records
            if item.provider == key
        )

    def by_subject(
        self,
        subject: str,
    ) -> tuple[ReasoningEvidenceRegistryRecord, ...]:
        key = " ".join(str(subject).strip().split())
        return tuple(
            item
            for item in self._records
            if item.subject == key
        )

    def by_observation_type(
        self,
        observation_type: str,
    ) -> tuple[ReasoningEvidenceRegistryRecord, ...]:
        key = " ".join(
            str(observation_type).strip().lower().split()
        )
        return tuple(
            item
            for item in self._records
            if item.observation_type == key
        )


def verify_reasoning_evidence_registry() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-037 must remain read-only"
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
        )
    ):
        raise AssertionError(
            "OI-037 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_037_REVISION",
    "ReasoningEvidenceRegistryError",
    "ReasoningEvidenceRegistryRecord",
    "ReasoningEvidenceRegistry",
    "verify_reasoning_evidence_registry",
]
