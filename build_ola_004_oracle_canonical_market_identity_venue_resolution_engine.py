from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parent

PACKAGE_DIR = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
)

MODULE_PATH = (
    PACKAGE_DIR
    / "oracle_canonical_market_identity_venue_resolution_engine.py"
)

PACKAGE_INIT_PATH = PACKAGE_DIR / "__init__.py"

TEST_PATH = (
    ROOT
    / "test_ola_004_oracle_canonical_market_identity_venue_resolution_engine.py"
)


MODULE_CONTENT = r'''
"""
OLA-004
Oracle Canonical Market Identity and Venue Resolution Engine

Read-only canonical market identity and verified venue resolution boundary.

Architecture:

SOURCE MARKET RECORD
    |
CANONICAL MARKET IDENTITY
    |
VERIFIED VENUE RESOLUTION
    |
CANONICAL MARKET / VENUE RECORD
    |
ORACLE OPPORTUNITY INTELLIGENCE
    |
Q SERIES INTAKE

Permanent rules:

- Oracle may resolve identity and venue as intelligence evidence.
- Oracle may not select or invoke execution adapters.
- A venue must be explicitly approved.
- A source-native market identifier must be preserved.
- Ambiguous venue evidence fails closed.
- Conflicting venue evidence fails closed.
- Unresolved venue evidence remains unresolved.
- No default venue exists.
- No fallback execution adapter exists.
- Canonical records use caller-supplied timestamps.
- Canonical stable hashing is used.
- repr() is never used.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from typing import Any, Mapping


SCHEMA_VERSION = "OLA-004"
ENGINE_ID = "OLA-004"

MARKET_IDENTITY_RECORD_TYPE = "canonical_market_identity"
VENUE_RESOLUTION_RECORD_TYPE = "verified_venue_resolution"
MARKET_VENUE_RECORD_TYPE = "canonical_market_venue_record"


JSONScalar = None | bool | int | float | str
JSONValue = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]


class MarketIdentityContractError(ValueError):
    """Raised when canonical market identity data is malformed."""


class VenueResolutionError(ValueError):
    """Raised when venue evidence cannot be safely resolved."""


class VenueResolutionInvariantError(RuntimeError):
    """Raised when permanent no-execution invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise MarketIdentityContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise MarketIdentityContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise MarketIdentityContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise MarketIdentityContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _canonicalize(value: Any) -> JSONValue:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise MarketIdentityContractError(
                "non-finite floats are not canonical"
            )

        return json.loads(
            json.dumps(
                value,
                allow_nan=False,
            )
        )

    if isinstance(value, datetime):
        return _require_aware_datetime(
            value,
            "canonical datetime",
        ).isoformat()

    if isinstance(value, str):
        return value

    if isinstance(value, Mapping):
        result: dict[str, JSONValue] = {}

        for key in sorted(value.keys()):
            if not isinstance(key, str):
                raise MarketIdentityContractError(
                    "canonical mapping keys must be strings"
                )

            result[key] = _canonicalize(value[key])

        return result

    if isinstance(value, (list, tuple)):
        return [
            _canonicalize(item)
            for item in value
        ]

    raise MarketIdentityContractError(
        "unsupported canonical value type: "
        f"{type(value).__name__}"
    )


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def stable_hash(value: Any) -> str:
    return sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def _immutable_mapping(
    value: Mapping[str, Any],
    field_name: str,
) -> tuple[tuple[str, JSONValue], ...]:
    if not isinstance(value, Mapping):
        raise MarketIdentityContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(value)

    if not isinstance(canonical, dict):
        raise MarketIdentityContractError(
            f"{field_name} must canonicalize to a mapping"
        )

    return tuple(
        (key, canonical[key])
        for key in sorted(canonical)
    )


def _mapping_from_immutable(
    value: tuple[tuple[str, JSONValue], ...],
) -> dict[str, JSONValue]:
    return {
        key: item
        for key, item in value
    }


def _immutable_strings(
    values: Any,
    field_name: str,
) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise MarketIdentityContractError(
            f"{field_name} must be a list or tuple"
        )

    normalized = tuple(
        _require_non_empty_string(
            value,
            field_name,
        )
        for value in values
    )

    if len(set(normalized)) != len(normalized):
        raise MarketIdentityContractError(
            f"{field_name} must not contain duplicates"
        )

    return tuple(sorted(normalized))


@dataclass(frozen=True, slots=True)
class ApprovedVenueRegistration:
    venue_id: str
    venue_name: str
    venue_type: str
    source_ids: tuple[str, ...]
    registration_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    registration_hash: str

    @classmethod
    def create(
        cls,
        *,
        venue_id: str,
        venue_name: str,
        venue_type: str,
        source_ids: list[str] | tuple[str, ...],
        registration_metadata: Mapping[str, Any],
    ) -> "ApprovedVenueRegistration":
        normalized_venue_id = _require_non_empty_string(
            venue_id,
            "venue_id",
        )

        normalized_venue_name = _require_non_empty_string(
            venue_name,
            "venue_name",
        )

        normalized_venue_type = _require_non_empty_string(
            venue_type,
            "venue_type",
        )

        normalized_source_ids = _immutable_strings(
            source_ids,
            "source_ids",
        )

        if not normalized_source_ids:
            raise MarketIdentityContractError(
                "source_ids must not be empty"
            )

        metadata = _immutable_mapping(
            registration_metadata,
            "registration_metadata",
        )

        payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "approved_venue_registration",
            "venue_id": normalized_venue_id,
            "venue_name": normalized_venue_name,
            "venue_type": normalized_venue_type,
            "source_ids": normalized_source_ids,
            "registration_metadata": (
                _mapping_from_immutable(metadata)
            ),
        }

        return cls(
            venue_id=normalized_venue_id,
            venue_name=normalized_venue_name,
            venue_type=normalized_venue_type,
            source_ids=normalized_source_ids,
            registration_metadata=metadata,
            registration_hash=stable_hash(payload),
        )


@dataclass(frozen=True, slots=True)
class SourceMarketIdentityEvidence:
    source_id: str
    source_market_id: str
    source_symbol: str
    instrument_type: str
    market_title: str
    venue_claim: str
    identity_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    observed_at: datetime
    evidence_hash: str

    @classmethod
    def create(
        cls,
        *,
        source_id: str,
        source_market_id: str,
        source_symbol: str,
        instrument_type: str,
        market_title: str,
        venue_claim: str,
        identity_metadata: Mapping[str, Any],
        observed_at: datetime,
    ) -> "SourceMarketIdentityEvidence":
        normalized_source_id = _require_non_empty_string(
            source_id,
            "source_id",
        )

        normalized_source_market_id = _require_non_empty_string(
            source_market_id,
            "source_market_id",
        )

        normalized_source_symbol = _require_non_empty_string(
            source_symbol,
            "source_symbol",
        )

        normalized_instrument_type = _require_non_empty_string(
            instrument_type,
            "instrument_type",
        )

        normalized_market_title = _require_non_empty_string(
            market_title,
            "market_title",
        )

        normalized_venue_claim = _require_non_empty_string(
            venue_claim,
            "venue_claim",
        )

        metadata = _immutable_mapping(
            identity_metadata,
            "identity_metadata",
        )

        normalized_observed_at = _require_aware_datetime(
            observed_at,
            "observed_at",
        )

        payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "source_market_identity_evidence",
            "source_id": normalized_source_id,
            "source_market_id": normalized_source_market_id,
            "source_symbol": normalized_source_symbol,
            "instrument_type": normalized_instrument_type,
            "market_title": normalized_market_title,
            "venue_claim": normalized_venue_claim,
            "identity_metadata": _mapping_from_immutable(
                metadata
            ),
            "observed_at": normalized_observed_at,
        }

        return cls(
            source_id=normalized_source_id,
            source_market_id=normalized_source_market_id,
            source_symbol=normalized_source_symbol,
            instrument_type=normalized_instrument_type,
            market_title=normalized_market_title,
            venue_claim=normalized_venue_claim,
            identity_metadata=metadata,
            observed_at=normalized_observed_at,
            evidence_hash=stable_hash(payload),
        )


@dataclass(frozen=True, slots=True)
class CanonicalMarketIdentity:
    schema_version: str
    engine_id: str
    canonical_market_id: str
    source_id: str
    source_market_id: str
    source_symbol: str
    instrument_type: str
    market_title: str
    observed_at: datetime
    resolved_at: datetime
    source_evidence_hash: str
    identity_hash: str
    immutable: bool
    read_only: bool

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "canonical_market_id": self.canonical_market_id,
            "source_id": self.source_id,
            "source_market_id": self.source_market_id,
            "source_symbol": self.source_symbol,
            "instrument_type": self.instrument_type,
            "market_title": self.market_title,
            "observed_at": self.observed_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat(),
            "source_evidence_hash": self.source_evidence_hash,
            "identity_hash": self.identity_hash,
            "immutable": self.immutable,
            "read_only": self.read_only,
        }


@dataclass(frozen=True, slots=True)
class VerifiedVenueResolution:
    schema_version: str
    engine_id: str
    canonical_market_id: str
    venue_id: str | None
    venue_name: str | None
    venue_type: str | None
    resolution_status: str
    reason_codes: tuple[str, ...]
    source_id: str
    source_venue_claim: str
    approved_registration_hash: str | None
    resolved_at: datetime
    resolution_hash: str
    venue_verified: bool
    default_venue_used: bool
    fallback_adapter_used: bool
    execution_adapter_resolved: bool
    read_only: bool
    execution_allowed: bool

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "canonical_market_id": self.canonical_market_id,
            "venue_id": self.venue_id,
            "venue_name": self.venue_name,
            "venue_type": self.venue_type,
            "resolution_status": self.resolution_status,
            "reason_codes": list(self.reason_codes),
            "source_id": self.source_id,
            "source_venue_claim": self.source_venue_claim,
            "approved_registration_hash": (
                self.approved_registration_hash
            ),
            "resolved_at": self.resolved_at.isoformat(),
            "resolution_hash": self.resolution_hash,
            "venue_verified": self.venue_verified,
            "default_venue_used": self.default_venue_used,
            "fallback_adapter_used": self.fallback_adapter_used,
            "execution_adapter_resolved": (
                self.execution_adapter_resolved
            ),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
        }


@dataclass(frozen=True, slots=True)
class CanonicalMarketVenueRecord:
    schema_version: str
    engine_id: str
    canonical_market_identity: CanonicalMarketIdentity
    venue_resolution: VerifiedVenueResolution
    record_hash: str
    replayable: bool
    auditable: bool
    explainable: bool
    read_only: bool
    execution_allowed: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    execution_adapter_invocation_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "canonical_market_identity": (
                self.canonical_market_identity.to_canonical_dict()
            ),
            "venue_resolution": (
                self.venue_resolution.to_canonical_dict()
            ),
            "record_hash": self.record_hash,
            "replayable": self.replayable,
            "auditable": self.auditable,
            "explainable": self.explainable,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "execution_adapter_invocation_allowed": (
                self.execution_adapter_invocation_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }


class OracleCanonicalMarketIdentityVenueResolutionEngine:
    """
    Resolves source-native market identity and verified venue identity.

    This engine intentionally does not know execution adapter mappings.
    Adapter resolution belongs to Q Series.
    """

    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID

    read_only = True
    execution_allowed = False
    trade_authorization_allowed = False
    order_placement_allowed = False
    execution_adapter_invocation_allowed = False
    funds_moved = False
    portfolio_mutated = False

    def __init__(
        self,
        *,
        approved_venues: (
            list[ApprovedVenueRegistration]
            | tuple[ApprovedVenueRegistration, ...]
        ),
    ) -> None:
        if not isinstance(approved_venues, (list, tuple)):
            raise MarketIdentityContractError(
                "approved_venues must be a list or tuple"
            )

        self._approved_venues: dict[
            str,
            ApprovedVenueRegistration,
        ] = {}

        for registration in approved_venues:
            if not isinstance(
                registration,
                ApprovedVenueRegistration,
            ):
                raise MarketIdentityContractError(
                    "approved_venues contains incompatible record"
                )

            if registration.venue_id in self._approved_venues:
                raise MarketIdentityContractError(
                    "duplicate approved venue_id"
                )

            self._approved_venues[
                registration.venue_id
            ] = registration

        self._assert_invariants()

    def _assert_invariants(self) -> None:
        actual = {
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "execution_adapter_invocation_allowed": (
                self.execution_adapter_invocation_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }

        expected = {
            "read_only": True,
            "execution_allowed": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "execution_adapter_invocation_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        if actual != expected:
            raise VenueResolutionInvariantError(
                "Oracle venue resolution invariants violated"
            )

    def resolve(
        self,
        *,
        evidence: SourceMarketIdentityEvidence,
        resolved_at: datetime,
    ) -> CanonicalMarketVenueRecord:
        self._assert_invariants()

        if not isinstance(
            evidence,
            SourceMarketIdentityEvidence,
        ):
            raise MarketIdentityContractError(
                "evidence must be SourceMarketIdentityEvidence"
            )

        normalized_resolved_at = _require_aware_datetime(
            resolved_at,
            "resolved_at",
        )

        if normalized_resolved_at < evidence.observed_at:
            raise MarketIdentityContractError(
                "resolved_at cannot be before observed_at"
            )

        identity = self._build_identity(
            evidence=evidence,
            resolved_at=normalized_resolved_at,
        )

        venue_resolution = self._resolve_venue(
            identity=identity,
            evidence=evidence,
            resolved_at=normalized_resolved_at,
        )

        return self._build_record(
            identity=identity,
            venue_resolution=venue_resolution,
        )

    def _build_identity(
        self,
        *,
        evidence: SourceMarketIdentityEvidence,
        resolved_at: datetime,
    ) -> CanonicalMarketIdentity:
        canonical_market_id = "market." + stable_hash(
            {
                "source_id": evidence.source_id,
                "source_market_id": evidence.source_market_id,
                "source_symbol": evidence.source_symbol,
                "instrument_type": evidence.instrument_type,
            }
        )

        identity_payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": MARKET_IDENTITY_RECORD_TYPE,
            "canonical_market_id": canonical_market_id,
            "source_id": evidence.source_id,
            "source_market_id": evidence.source_market_id,
            "source_symbol": evidence.source_symbol,
            "instrument_type": evidence.instrument_type,
            "market_title": evidence.market_title,
            "observed_at": evidence.observed_at,
            "resolved_at": resolved_at,
            "source_evidence_hash": evidence.evidence_hash,
            "immutable": True,
            "read_only": True,
        }

        return CanonicalMarketIdentity(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            canonical_market_id=canonical_market_id,
            source_id=evidence.source_id,
            source_market_id=evidence.source_market_id,
            source_symbol=evidence.source_symbol,
            instrument_type=evidence.instrument_type,
            market_title=evidence.market_title,
            observed_at=evidence.observed_at,
            resolved_at=resolved_at,
            source_evidence_hash=evidence.evidence_hash,
            identity_hash=stable_hash(identity_payload),
            immutable=True,
            read_only=True,
        )

    def _resolve_venue(
        self,
        *,
        identity: CanonicalMarketIdentity,
        evidence: SourceMarketIdentityEvidence,
        resolved_at: datetime,
    ) -> VerifiedVenueResolution:
        candidates = []

        for registration in self._approved_venues.values():
            source_match = (
                evidence.source_id
                in registration.source_ids
            )

            venue_claim_match = (
                evidence.venue_claim
                == registration.venue_id
            )

            if source_match and venue_claim_match:
                candidates.append(registration)

        if len(candidates) > 1:
            raise VenueResolutionError(
                "ambiguous approved venue resolution"
            )

        if len(candidates) == 0:
            venue_id = None
            venue_name = None
            venue_type = None
            resolution_status = "unresolved"
            reason_codes = (
                "approved_venue_match_not_found",
                "venue_unresolved",
            )
            registration_hash = None
            venue_verified = False
        else:
            registration = candidates[0]

            venue_id = registration.venue_id
            venue_name = registration.venue_name
            venue_type = registration.venue_type
            resolution_status = "verified"
            reason_codes = (
                "source_identity_matched",
                "venue_claim_matched",
                "venue_registration_approved",
                "venue_verified",
            )
            registration_hash = (
                registration.registration_hash
            )
            venue_verified = True

        resolution_payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": VENUE_RESOLUTION_RECORD_TYPE,
            "canonical_market_id": identity.canonical_market_id,
            "venue_id": venue_id,
            "venue_name": venue_name,
            "venue_type": venue_type,
            "resolution_status": resolution_status,
            "reason_codes": reason_codes,
            "source_id": evidence.source_id,
            "source_venue_claim": evidence.venue_claim,
            "approved_registration_hash": registration_hash,
            "resolved_at": resolved_at,
            "venue_verified": venue_verified,
            "default_venue_used": False,
            "fallback_adapter_used": False,
            "execution_adapter_resolved": False,
            "read_only": True,
            "execution_allowed": False,
        }

        return VerifiedVenueResolution(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            canonical_market_id=identity.canonical_market_id,
            venue_id=venue_id,
            venue_name=venue_name,
            venue_type=venue_type,
            resolution_status=resolution_status,
            reason_codes=reason_codes,
            source_id=evidence.source_id,
            source_venue_claim=evidence.venue_claim,
            approved_registration_hash=registration_hash,
            resolved_at=resolved_at,
            resolution_hash=stable_hash(
                resolution_payload
            ),
            venue_verified=venue_verified,
            default_venue_used=False,
            fallback_adapter_used=False,
            execution_adapter_resolved=False,
            read_only=True,
            execution_allowed=False,
        )

    def _build_record(
        self,
        *,
        identity: CanonicalMarketIdentity,
        venue_resolution: VerifiedVenueResolution,
    ) -> CanonicalMarketVenueRecord:
        record_payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": MARKET_VENUE_RECORD_TYPE,
            "canonical_market_identity": (
                identity.to_canonical_dict()
            ),
            "venue_resolution": (
                venue_resolution.to_canonical_dict()
            ),
            "replayable": True,
            "auditable": True,
            "explainable": True,
            "read_only": True,
            "execution_allowed": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "execution_adapter_invocation_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        return CanonicalMarketVenueRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            canonical_market_identity=identity,
            venue_resolution=venue_resolution,
            record_hash=stable_hash(record_payload),
            replayable=True,
            auditable=True,
            explainable=True,
            read_only=True,
            execution_allowed=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            execution_adapter_invocation_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "MarketIdentityContractError",
    "VenueResolutionError",
    "VenueResolutionInvariantError",
    "ApprovedVenueRegistration",
    "SourceMarketIdentityEvidence",
    "CanonicalMarketIdentity",
    "VerifiedVenueResolution",
    "CanonicalMarketVenueRecord",
    "OracleCanonicalMarketIdentityVenueResolutionEngine",
    "canonical_json",
    "stable_hash",
]
'''


PACKAGE_INIT_CONTENT = r'''
"""
Oracle live read-only acquisition subsystem.
"""

from .oracle_live_read_only_acquisition_runtime import (
    AcquisitionBatchRecord,
    AcquisitionContractError,
    AcquisitionInvariantError,
    AcquisitionObservationRecord,
    ApprovedReadOnlySourceAdapter,
    ApprovedSourceAdapterRegistration,
    CanonicalObservation,
    CanonicalObservationRouterFailure,
    DeduplicationEvidence,
    ObservationRoutingEvidence,
    OracleLiveReadOnlyAcquisitionRuntime,
    RateControlEvidence,
    RawSourceObservation,
    SourceAdapterFailure,
    SourceHealthEvidence,
    UnapprovedSourceAdapterError,
)

from .oracle_acquisition_source_control_engine import (
    OracleAcquisitionSourceControlEngine,
    RateControlPolicy,
    RateWindowObservation,
    SourceControlContractError,
    SourceControlDecisionRecord,
    SourceControlInvariantError,
    SourceControlPolicyError,
    SourceHealthObservation,
    SourceHealthPolicy,
)

from .oracle_acquisition_deduplication_ledger import (
    CanonicalDeduplicationLedgerEntry,
    DeduplicationLedgerContractError,
    DeduplicationLedgerInvariantError,
    DeduplicationLedgerSnapshot,
    DeduplicationLedgerSnapshotError,
    OracleAcquisitionDeduplicationLedger,
)

from .oracle_canonical_market_identity_venue_resolution_engine import (
    ApprovedVenueRegistration,
    CanonicalMarketIdentity,
    CanonicalMarketVenueRecord,
    MarketIdentityContractError,
    OracleCanonicalMarketIdentityVenueResolutionEngine,
    SourceMarketIdentityEvidence,
    VenueResolutionError,
    VenueResolutionInvariantError,
    VerifiedVenueResolution,
)

__all__ = [
    "AcquisitionBatchRecord",
    "AcquisitionContractError",
    "AcquisitionInvariantError",
    "AcquisitionObservationRecord",
    "ApprovedReadOnlySourceAdapter",
    "ApprovedSourceAdapterRegistration",
    "CanonicalObservation",
    "CanonicalObservationRouterFailure",
    "DeduplicationEvidence",
    "ObservationRoutingEvidence",
    "OracleLiveReadOnlyAcquisitionRuntime",
    "RateControlEvidence",
    "RawSourceObservation",
    "SourceAdapterFailure",
    "SourceHealthEvidence",
    "UnapprovedSourceAdapterError",
    "OracleAcquisitionSourceControlEngine",
    "RateControlPolicy",
    "RateWindowObservation",
    "SourceControlContractError",
    "SourceControlDecisionRecord",
    "SourceControlInvariantError",
    "SourceControlPolicyError",
    "SourceHealthObservation",
    "SourceHealthPolicy",
    "CanonicalDeduplicationLedgerEntry",
    "DeduplicationLedgerContractError",
    "DeduplicationLedgerInvariantError",
    "DeduplicationLedgerSnapshot",
    "DeduplicationLedgerSnapshotError",
    "OracleAcquisitionDeduplicationLedger",
    "ApprovedVenueRegistration",
    "CanonicalMarketIdentity",
    "CanonicalMarketVenueRecord",
    "MarketIdentityContractError",
    "OracleCanonicalMarketIdentityVenueResolutionEngine",
    "SourceMarketIdentityEvidence",
    "VenueResolutionError",
    "VenueResolutionInvariantError",
    "VerifiedVenueResolution",
]
'''


TEST_CONTENT = r'''
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition import (
    ApprovedVenueRegistration,
    OracleCanonicalMarketIdentityVenueResolutionEngine,
    SourceMarketIdentityEvidence,
)


OBSERVED_AT = datetime(
    2026,
    7,
    11,
    22,
    10,
    0,
    tzinfo=timezone.utc,
)

RESOLVED_AT = datetime(
    2026,
    7,
    11,
    22,
    10,
    1,
    tzinfo=timezone.utc,
)


def build_engine():
    kalshi = ApprovedVenueRegistration.create(
        venue_id="venue.kalshi",
        venue_name="Kalshi",
        venue_type="prediction_market",
        source_ids=(
            "source.kalshi.market_data",
        ),
        registration_metadata={
            "approved": True,
            "market_identity_required": True,
        },
    )

    coinbase = ApprovedVenueRegistration.create(
        venue_id="venue.coinbase",
        venue_name="Coinbase",
        venue_type="crypto_spot",
        source_ids=(
            "source.coinbase.market_data",
        ),
        registration_metadata={
            "approved": True,
            "market_identity_required": True,
        },
    )

    return (
        OracleCanonicalMarketIdentityVenueResolutionEngine(
            approved_venues=(
                kalshi,
                coinbase,
            ),
        )
    )


def build_kalshi_evidence():
    return SourceMarketIdentityEvidence.create(
        source_id="source.kalshi.market_data",
        source_market_id="KXBTC-26JUL11-116000",
        source_symbol="KXBTC-26JUL11-116000",
        instrument_type="prediction_contract",
        market_title="Bitcoin below 116000 by 5 PM",
        venue_claim="venue.kalshi",
        identity_metadata={
            "settlement_currency": "USD",
            "contract_sides": ["yes", "no"],
        },
        observed_at=OBSERVED_AT,
    )


def run_verified_resolution_test():
    engine = build_engine()

    evidence = build_kalshi_evidence()

    first = engine.resolve(
        evidence=evidence,
        resolved_at=RESOLVED_AT,
    )

    second = engine.resolve(
        evidence=evidence,
        resolved_at=RESOLVED_AT,
    )

    identity = first.canonical_market_identity
    venue = first.venue_resolution

    assert first.schema_version == "OLA-004"
    assert first.engine_id == "OLA-004"

    assert identity.source_id == (
        "source.kalshi.market_data"
    )

    assert identity.source_market_id == (
        "KXBTC-26JUL11-116000"
    )

    assert identity.source_symbol == (
        "KXBTC-26JUL11-116000"
    )

    assert identity.instrument_type == (
        "prediction_contract"
    )

    assert identity.canonical_market_id.startswith(
        "market."
    )

    assert identity.immutable is True
    assert identity.read_only is True

    assert venue.resolution_status == "verified"
    assert venue.venue_verified is True
    assert venue.venue_id == "venue.kalshi"
    assert venue.venue_name == "Kalshi"

    assert venue.default_venue_used is False
    assert venue.fallback_adapter_used is False

    assert (
        venue.execution_adapter_resolved
        is False
    )

    assert first.record_hash == second.record_hash

    assert (
        first.canonical_market_identity.identity_hash
        == second.canonical_market_identity.identity_hash
    )

    assert (
        first.venue_resolution.resolution_hash
        == second.venue_resolution.resolution_hash
    )

    assert first.replayable is True
    assert first.auditable is True
    assert first.explainable is True

    assert first.read_only is True
    assert first.execution_allowed is False

    assert (
        first.trade_authorization_allowed
        is False
    )

    assert first.order_placement_allowed is False

    assert (
        first.execution_adapter_invocation_allowed
        is False
    )

    assert first.funds_moved is False
    assert first.portfolio_mutated is False

    try:
        venue.venue_id = "venue.coinbase"
        raise AssertionError(
            "venue resolution must be immutable"
        )
    except FrozenInstanceError:
        pass

    return first


def run_unresolved_fail_closed_test():
    engine = build_engine()

    evidence = SourceMarketIdentityEvidence.create(
        source_id="source.unknown.market_data",
        source_market_id="UNKNOWN-1",
        source_symbol="UNKNOWN-1",
        instrument_type="prediction_contract",
        market_title="Unknown source market",
        venue_claim="venue.unknown",
        identity_metadata={},
        observed_at=OBSERVED_AT,
    )

    record = engine.resolve(
        evidence=evidence,
        resolved_at=RESOLVED_AT,
    )

    venue = record.venue_resolution

    assert venue.resolution_status == "unresolved"
    assert venue.venue_verified is False

    assert venue.venue_id is None
    assert venue.venue_name is None
    assert venue.venue_type is None

    assert venue.default_venue_used is False
    assert venue.fallback_adapter_used is False

    assert (
        venue.execution_adapter_resolved
        is False
    )

    assert record.execution_allowed is False

    return record


def run_conflicting_claim_test():
    engine = build_engine()

    evidence = SourceMarketIdentityEvidence.create(
        source_id="source.kalshi.market_data",
        source_market_id="KXBTC-CONFLICT",
        source_symbol="KXBTC-CONFLICT",
        instrument_type="prediction_contract",
        market_title="Conflicting venue claim",
        venue_claim="venue.coinbase",
        identity_metadata={},
        observed_at=OBSERVED_AT,
    )

    record = engine.resolve(
        evidence=evidence,
        resolved_at=RESOLVED_AT,
    )

    venue = record.venue_resolution

    assert venue.resolution_status == "unresolved"
    assert venue.venue_verified is False
    assert venue.venue_id is None

    assert (
        "approved_venue_match_not_found"
        in venue.reason_codes
    )

    return record


def run_timestamp_fail_closed_test():
    engine = build_engine()

    evidence = build_kalshi_evidence()

    try:
        engine.resolve(
            evidence=evidence,
            resolved_at=datetime(
                2026,
                7,
                11,
                22,
                10,
                1,
            ),
        )

        raise AssertionError(
            "naive resolved_at must fail closed"
        )
    except ValueError:
        pass


def main():
    verified = run_verified_resolution_test()
    unresolved = run_unresolved_fail_closed_test()
    conflicting = run_conflicting_claim_test()
    run_timestamp_fail_closed_test()

    result = {
        "schema_version": verified.schema_version,
        "engine_id": verified.engine_id,
        "status": "passed",
        "canonical_market_id": (
            verified
            .canonical_market_identity
            .canonical_market_id
        ),
        "venue_resolution_status": (
            verified
            .venue_resolution
            .resolution_status
        ),
        "venue_id": (
            verified
            .venue_resolution
            .venue_id
        ),
        "venue_verified": (
            verified
            .venue_resolution
            .venue_verified
        ),
        "unresolved_market_blocked": (
            unresolved
            .venue_resolution
            .venue_verified
            is False
        ),
        "conflicting_claim_blocked": (
            conflicting
            .venue_resolution
            .venue_verified
            is False
        ),
        "default_venue_used": (
            verified
            .venue_resolution
            .default_venue_used
        ),
        "fallback_adapter_used": (
            verified
            .venue_resolution
            .fallback_adapter_used
        ),
        "execution_adapter_resolved": (
            verified
            .venue_resolution
            .execution_adapter_resolved
        ),
        "read_only": verified.read_only,
        "execution_allowed": (
            verified.execution_allowed
        ),
        "trade_authorization_allowed": (
            verified.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            verified.order_placement_allowed
        ),
        "execution_adapter_invocation_allowed": (
            verified
            .execution_adapter_invocation_allowed
        ),
        "funds_moved": verified.funds_moved,
        "portfolio_mutated": verified.portfolio_mutated,
    }

    print(
        "[PASS] OLA-004 Oracle Canonical Market "
        "Identity and Venue Resolution Engine"
    )

    print(result)


if __name__ == "__main__":
    main()
'''


def write_file(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        textwrap.dedent(content).lstrip(),
        encoding="utf-8",
    )

    print(f"[OK] Wrote {path}")


def main() -> None:
    print("========================================")
    print(" OLA-004 INSTALLER")
    print(" Oracle Canonical Market Identity")
    print(" and Venue Resolution Engine")
    print("========================================")

    write_file(
        MODULE_PATH,
        MODULE_CONTENT,
    )

    write_file(
        PACKAGE_INIT_PATH,
        PACKAGE_INIT_CONTENT,
    )

    write_file(
        TEST_PATH,
        TEST_CONTENT,
    )

    print()
    print("[DONE] OLA-004 installed")
    print()
    print("Run:")
    print(
        "py test_ola_004_oracle_canonical_market_"
        "identity_venue_resolution_engine.py"
    )


if __name__ == "__main__":
    main()