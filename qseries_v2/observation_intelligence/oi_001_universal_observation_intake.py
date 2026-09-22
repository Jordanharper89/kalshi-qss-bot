from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping


BUILD_ID = "OI-001"

OI_001_REVISION = (
    "OI_001_UNIVERSAL_OBSERVATION_INTAKE_FOUNDATION_V1"
)

SCHEMA_VERSION = "1.0.0"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False


SUPPORTED_SOURCE_KINDS = (
    "market_venue",
    "market_data",
    "weather",
    "economic",
    "news",
    "regulatory",
    "blockchain",
    "sports",
    "corporate",
    "scientific",
    "government",
    "other",
)


class ObservationIntakeContractError(ValueError):
    pass


def _normalize_text(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise ObservationIntakeContractError(
            f"{field} must be a string"
        )

    normalized = " ".join(value.strip().split())

    if not normalized:
        raise ObservationIntakeContractError(
            f"{field} must not be empty"
        )

    return normalized


def _utc_timestamp(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ObservationIntakeContractError(
            "observed_at must be datetime"
        )

    if value.tzinfo is None:
        raise ObservationIntakeContractError(
            "observed_at must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _canonicalize(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonicalize(asdict(value))

    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if isinstance(value, (tuple, list)):
        return [
            _canonicalize(item)
            for item in value
        ]

    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ObservationIntakeContractError(
                "canonical datetime must be timezone-aware"
            )

        return value.astimezone(
            timezone.utc
        ).isoformat()

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    raise ObservationIntakeContractError(
        f"unsupported canonical value type: {type(value)!r}"
    )


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def deterministic_sha256(value: Any) -> str:
    return hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class ObservationSourceIdentity:
    source_id: str
    source_kind: str
    provider: str
    adapter_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_id",
            _normalize_text(
                self.source_id,
                "source_id",
            ).lower(),
        )

        kind = _normalize_text(
            self.source_kind,
            "source_kind",
        ).lower()

        if kind not in SUPPORTED_SOURCE_KINDS:
            raise ObservationIntakeContractError(
                "unsupported source_kind"
            )

        object.__setattr__(
            self,
            "source_kind",
            kind,
        )

        object.__setattr__(
            self,
            "provider",
            _normalize_text(
                self.provider,
                "provider",
            ),
        )

        object.__setattr__(
            self,
            "adapter_id",
            _normalize_text(
                self.adapter_id,
                "adapter_id",
            ).lower(),
        )

    @property
    def source_hash(self) -> str:
        return deterministic_sha256(
            {
                "source_id": self.source_id,
                "source_kind": self.source_kind,
                "provider": self.provider,
                "adapter_id": self.adapter_id,
            }
        )


@dataclass(frozen=True, slots=True)
class RawObservationEnvelope:
    source: ObservationSourceIdentity
    external_observation_id: str
    observed_at: datetime
    subject: str
    observation_type: str
    payload: Mapping[str, Any]
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(
            self.source,
            ObservationSourceIdentity,
        ):
            raise ObservationIntakeContractError(
                "source must be ObservationSourceIdentity"
            )

        object.__setattr__(
            self,
            "external_observation_id",
            _normalize_text(
                self.external_observation_id,
                "external_observation_id",
            ),
        )

        object.__setattr__(
            self,
            "observed_at",
            _utc_timestamp(
                self.observed_at
            ),
        )

        object.__setattr__(
            self,
            "subject",
            _normalize_text(
                self.subject,
                "subject",
            ),
        )

        object.__setattr__(
            self,
            "observation_type",
            _normalize_text(
                self.observation_type,
                "observation_type",
            ).lower(),
        )

        payload = dict(self.payload)
        metadata = dict(self.metadata)

        canonical_json(payload)
        canonical_json(metadata)

        object.__setattr__(
            self,
            "payload",
            MappingProxyType(payload),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(metadata),
        )

    @property
    def envelope_hash(self) -> str:
        return deterministic_sha256(
            {
                "source_hash": self.source.source_hash,
                "external_observation_id": (
                    self.external_observation_id
                ),
                "observed_at": self.observed_at,
                "subject": self.subject,
                "observation_type": (
                    self.observation_type
                ),
                "payload": dict(self.payload),
                "metadata": dict(self.metadata),
            }
        )


@dataclass(frozen=True, slots=True)
class ObservationIntakeReceipt:
    envelope_hash: str
    source_hash: str
    accepted: bool
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        for value, field in (
            (self.envelope_hash, "envelope_hash"),
            (self.source_hash, "source_hash"),
        ):
            if (
                not isinstance(value, str)
                or len(value) != 64
                or any(
                    c not in "0123456789abcdef"
                    for c in value
                )
            ):
                raise ObservationIntakeContractError(
                    f"{field} must be lowercase SHA-256"
                )

        reasons = tuple(
            sorted(
                set(
                    _normalize_text(
                        reason,
                        "reason_code",
                    ).lower()
                    for reason in self.reason_codes
                )
            )
        )

        object.__setattr__(
            self,
            "reason_codes",
            reasons,
        )


class UniversalObservationIntake:
    read_only = True
    execution_allowed = False
    network_allowed = False
    persistence_allowed = False

    def accept(
        self,
        envelope: RawObservationEnvelope,
    ) -> ObservationIntakeReceipt:
        if not isinstance(
            envelope,
            RawObservationEnvelope,
        ):
            raise TypeError(
                "envelope must be RawObservationEnvelope"
            )

        return ObservationIntakeReceipt(
            envelope_hash=envelope.envelope_hash,
            source_hash=envelope.source.source_hash,
            accepted=True,
            reason_codes=(
                "contract_valid",
                "immutable_envelope",
                "source_identity_present",
                "timestamp_present",
            ),
        )


def verify_universal_observation_intake() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-001 must remain read-only"
        )

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-001 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_001_REVISION",
    "SCHEMA_VERSION",
    "SUPPORTED_SOURCE_KINDS",
    "ObservationIntakeContractError",
    "ObservationSourceIdentity",
    "RawObservationEnvelope",
    "ObservationIntakeReceipt",
    "UniversalObservationIntake",
    "canonical_json",
    "deterministic_sha256",
    "verify_universal_observation_intake",
]
