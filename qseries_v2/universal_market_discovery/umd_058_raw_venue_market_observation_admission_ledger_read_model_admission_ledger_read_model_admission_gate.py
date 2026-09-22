from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .umd_057_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model import (
    CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModel,
    certify_umd_057_read_model,
)

UMD_058_BUILD_ID = "UMD-058"
UMD_058_BUILD_NAME = (
    "Certified Raw Venue Market Observation Admission Ledger "
    "Read Model Admission Ledger Read Model Admission Gate"
)
UMD_058_REVISION = (
    "UMD_058_CERTIFIED_RAW_VENUE_MARKET_OBSERVATION_"
    "ADMISSION_LEDGER_READ_MODEL_ADMISSION_LEDGER_READ_MODEL_"
    "ADMISSION_GATE_V1"
)
UMD_058_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_invocation",
    "authentication_execution",
    "credential_storage",
    "automatic_discovery",
    "automatic_observation_creation",
    "automatic_admission_commit",
    "ledger_append",
    "ledger_mutation",
    "read_model_mutation",
    "read_model_persistence",
    "canonical_market_construction",
    "classification_inference",
    "duplicate_resolution",
    "registry_mutation",
    "oracle_memory_mutation",
    "publication",
    "order_submission",
    "trade_execution",
)


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _sha256(value: str, field_name: str) -> str:
    normalized = _text(value, field_name).lower()
    if len(normalized) != 64:
        raise ValueError(
            f"{field_name} must contain 64 hexadecimal characters"
        )
    if any(
        character not in "0123456789abcdef"
        for character in normalized
    ):
        raise ValueError(
            f"{field_name} must be lowercase SHA-256 hexadecimal"
        )
    return normalized


def _freeze_checks(
    checks: Mapping[str, bool],
) -> Mapping[str, bool]:
    if not isinstance(checks, Mapping):
        raise TypeError("checks must be a mapping")

    normalized = {}
    for key, value in checks.items():
        normalized_key = _text(
            str(key),
            "check name",
        )
        if not isinstance(value, bool):
            raise TypeError(
                f"check {normalized_key!r} must be boolean"
            )
        normalized[normalized_key] = value

    return MappingProxyType(
        dict(sorted(normalized.items()))
    )


def _reasons(
    values: Tuple[str, ...],
) -> Tuple[str, ...]:
    if not isinstance(values, tuple):
        values = tuple(values)
    return tuple(
        sorted(
            {
                _text(
                    value,
                    "rejection_reason",
                )
                for value in values
            }
        )
    )


@dataclass(frozen=True, slots=True)
class CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision:
    read_model_id: str
    read_model_hash: str
    source_ledger_hash: str
    total_entry_count: int
    admitted_entry_count: int
    rejected_entry_count: int
    latest_entry_id: str | None
    latest_admitted_entry_id: str | None
    admitted: bool
    checks: Mapping[str, bool]
    rejection_reasons: Tuple[str, ...]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "read_model_id",
            _text(
                self.read_model_id,
                "read_model_id",
            ),
        )
        object.__setattr__(
            self,
            "read_model_hash",
            _sha256(
                self.read_model_hash,
                "read_model_hash",
            ),
        )
        object.__setattr__(
            self,
            "source_ledger_hash",
            _sha256(
                self.source_ledger_hash,
                "source_ledger_hash",
            ),
        )

        for field_name in (
            "total_entry_count",
            "admitted_entry_count",
            "rejected_entry_count",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, int):
                raise TypeError(
                    f"{field_name} must be an integer"
                )
            if value < 0:
                raise ValueError(
                    f"{field_name} must be non-negative"
                )

        if (
            self.admitted_entry_count
            + self.rejected_entry_count
            != self.total_entry_count
        ):
            raise ValueError(
                "admitted and rejected counts must partition total"
            )

        for field_name in (
            "latest_entry_id",
            "latest_admitted_entry_id",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _text(
                        value,
                        field_name,
                    ),
                )

        if not isinstance(self.admitted, bool):
            raise TypeError(
                "admitted must be boolean"
            )

        frozen_checks = _freeze_checks(
            self.checks
        )
        object.__setattr__(
            self,
            "checks",
            frozen_checks,
        )

        normalized_reasons = _reasons(
            self.rejection_reasons
        )
        object.__setattr__(
            self,
            "rejection_reasons",
            normalized_reasons,
        )

        failed_checks = tuple(
            sorted(
                name
                for name, passed in frozen_checks.items()
                if not passed
            )
        )

        if self.admitted:
            if failed_checks:
                raise ValueError(
                    "admitted decisions cannot contain failed checks"
                )
            if normalized_reasons:
                raise ValueError(
                    "admitted decisions cannot contain rejection reasons"
                )
        else:
            if not failed_checks:
                raise ValueError(
                    "rejected decisions require failed checks"
                )
            if normalized_reasons != failed_checks:
                raise ValueError(
                    "rejection reasons must exactly match failed checks"
                )

        if (
            self.lineage.subsystem_id
            != UMD_SUBSYSTEM_ID
        ):
            raise ValueError(
                "decision lineage must belong to UMD"
            )
        if (
            self.lineage.build_id
            != UMD_058_BUILD_ID
        ):
            raise ValueError(
                "decision lineage must use build_id UMD-058"
            )
        if (
            self.read_model_hash
            not in self.lineage.parent_hashes
        ):
            raise ValueError(
                "decision lineage must include read_model_hash"
            )
        if (
            self.source_ledger_hash
            not in self.lineage.parent_hashes
        ):
            raise ValueError(
                "decision lineage must include source_ledger_hash"
            )

    @property
    def decision_id(self) -> str:
        return (
            "umd:raw-observation-admission-ledger-read-model-"
            "admission-ledger-read-model-admission-decision:"
            + deterministic_sha256(
                {
                    "read_model_id": self.read_model_id,
                    "read_model_hash": (
                        self.read_model_hash
                    ),
                    "source_ledger_hash": (
                        self.source_ledger_hash
                    ),
                    "admitted": self.admitted,
                    "checks": self.checks,
                    "rejection_reasons": (
                        self.rejection_reasons
                    ),
                }
            )
        )

    def to_canonical_dict(
        self,
    ) -> Mapping[str, Any]:
        return {
            "decision_id": self.decision_id,
            "read_model_id": self.read_model_id,
            "read_model_hash": self.read_model_hash,
            "source_ledger_hash": (
                self.source_ledger_hash
            ),
            "total_entry_count": (
                self.total_entry_count
            ),
            "admitted_entry_count": (
                self.admitted_entry_count
            ),
            "rejected_entry_count": (
                self.rejected_entry_count
            ),
            "latest_entry_id": (
                self.latest_entry_id
            ),
            "latest_admitted_entry_id": (
                self.latest_admitted_entry_id
            ),
            "admitted": self.admitted,
            "checks": self.checks,
            "rejection_reasons": (
                self.rejection_reasons
            ),
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def evaluate_umd_058_read_model_admission(
    read_model: CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModel,
    *,
    seen_read_model_ids: Tuple[str, ...] = (),
    seen_read_model_hashes: Tuple[str, ...] = (),
    seen_source_ledger_hashes: Tuple[str, ...] = (),
    lineage: ImmutableLineage,
) -> CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision:
    if not isinstance(
        read_model,
        CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModel,
    ):
        raise TypeError(
            "read_model must be the exact certified UMD-057 class"
        )

    certification = certify_umd_057_read_model(
        read_model
    )

    normalized_ids = {
        _text(
            value,
            "seen_read_model_id",
        )
        for value in seen_read_model_ids
    }
    normalized_hashes = {
        _sha256(
            value,
            "seen_read_model_hash",
        )
        for value in seen_read_model_hashes
    }
    normalized_source_hashes = {
        _sha256(
            value,
            "seen_source_ledger_hash",
        )
        for value in seen_source_ledger_hashes
    }

    checks = {
        "read_model_certified": (
            certification["certified"]
            is True
        ),
        "read_model_id_matches": (
            certification["read_model_id"]
            == read_model.read_model_id
        ),
        "read_model_hash_matches": (
            certification["read_model_hash"]
            == read_model.read_model_hash
        ),
        "source_ledger_hash_matches": (
            certification["source_ledger_hash"]
            == read_model.source_ledger_hash
        ),
        "counts_match": (
            certification["total_entry_count"]
            == read_model.total_entry_count
            and certification[
                "admitted_entry_count"
            ]
            == read_model.admitted_entry_count
            and certification[
                "rejected_entry_count"
            ]
            == read_model.rejected_entry_count
        ),
        "count_partition_valid": (
            read_model.admitted_entry_count
            + read_model.rejected_entry_count
            == read_model.total_entry_count
        ),
        "latest_entry_consistent": (
            (
                read_model.total_entry_count
                == 0
                and read_model.latest_entry_id
                is None
            )
            or (
                read_model.total_entry_count
                > 0
                and read_model.latest_entry_id
                == read_model.ordered_entry_ids[-1]
            )
        ),
        "latest_admitted_entry_consistent": (
            (
                read_model.admitted_entry_count
                == 0
                and read_model.latest_admitted_entry_id
                is None
            )
            or (
                read_model.admitted_entry_count
                > 0
                and read_model.latest_admitted_entry_id
                == read_model.admitted_entry_ids[-1]
            )
        ),
        "read_model_id_not_seen": (
            read_model.read_model_id
            not in normalized_ids
        ),
        "read_model_hash_not_seen": (
            read_model.read_model_hash
            not in normalized_hashes
        ),
        "source_ledger_hash_not_seen": (
            read_model.source_ledger_hash
            not in normalized_source_hashes
        ),
        "lineage_bound_to_source_ledger": (
            read_model.source_ledger_hash
            in read_model.lineage.parent_hashes
        ),
        "read_only_indexes": all(
            isinstance(
                index,
                MappingProxyType,
            )
            for index in (
                read_model._entry_position_by_id,
                read_model._read_model_position_by_id,
                read_model._read_model_position_by_hash,
                read_model._source_ledger_position_by_hash,
                read_model._decision_position_by_id,
            )
        ),
    }

    rejection_reasons = tuple(
        sorted(
            name
            for name, passed in checks.items()
            if not passed
        )
    )

    return CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision(
        read_model_id=read_model.read_model_id,
        read_model_hash=read_model.read_model_hash,
        source_ledger_hash=(
            read_model.source_ledger_hash
        ),
        total_entry_count=(
            read_model.total_entry_count
        ),
        admitted_entry_count=(
            read_model.admitted_entry_count
        ),
        rejected_entry_count=(
            read_model.rejected_entry_count
        ),
        latest_entry_id=(
            read_model.latest_entry_id
        ),
        latest_admitted_entry_id=(
            read_model.latest_admitted_entry_id
        ),
        admitted=not rejection_reasons,
        checks=checks,
        rejection_reasons=rejection_reasons,
        lineage=lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD058CertificationManifest:
    subsystem_id: str
    build_id: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    gate_mode: str
    prohibited_capabilities: Tuple[str, ...]
    network_enabled: bool
    persistence_enabled: bool
    mutation_enabled: bool
    publication_enabled: bool
    execution_enabled: bool

    def to_canonical_dict(
        self,
    ) -> Mapping[str, Any]:
        return {
            "subsystem_id": self.subsystem_id,
            "build_id": self.build_id,
            "revision": self.revision,
            "schema_version": (
                self.schema_version
            ),
            "upstream_builds": (
                self.upstream_builds
            ),
            "gate_mode": self.gate_mode,
            "prohibited_capabilities": (
                self.prohibited_capabilities
            ),
            "network_enabled": (
                self.network_enabled
            ),
            "persistence_enabled": (
                self.persistence_enabled
            ),
            "mutation_enabled": (
                self.mutation_enabled
            ),
            "publication_enabled": (
                self.publication_enabled
            ),
            "execution_enabled": (
                self.execution_enabled
            ),
        }

    @property
    def manifest_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def build_umd_058_certification_manifest(
) -> UMD058CertificationManifest:
    return UMD058CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_058_BUILD_ID,
        revision=UMD_058_REVISION,
        schema_version=(
            UMD_058_SCHEMA_VERSION
        ),
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 58)
        ),
        gate_mode=(
            "deterministic_read_only_read_model_admission"
        ),
        prohibited_capabilities=(
            PROHIBITED_CAPABILITIES
        ),
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_058_foundation(
) -> Mapping[str, Any]:
    manifest = build_umd_058_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-058"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 58)
            )
        ),
        "gate_mode": (
            manifest.gate_mode
            == "deterministic_read_only_read_model_admission"
        ),
        "network_disabled": (
            manifest.network_enabled is False
        ),
        "persistence_disabled": (
            manifest.persistence_enabled is False
        ),
        "mutation_disabled": (
            manifest.mutation_enabled is False
        ),
        "publication_disabled": (
            manifest.publication_enabled is False
        ),
        "execution_disabled": (
            manifest.execution_enabled is False
        ),
        "deterministic_manifest": (
            manifest.manifest_hash
            == deterministic_sha256(
                manifest.to_canonical_dict()
            )
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    return MappingProxyType(
        {
            "certified": not failed,
            "build_id": manifest.build_id,
            "revision": manifest.revision,
            "manifest_hash": (
                manifest.manifest_hash
            ),
            "checks": MappingProxyType(
                checks
            ),
            "failed_checks": failed,
        }
    )


def verify_umd_058_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_gate() -> bool:
    result = certify_umd_058_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-058 foundation certification failed: "
            + ", ".join(
                result["failed_checks"]
            )
        )
    return True
