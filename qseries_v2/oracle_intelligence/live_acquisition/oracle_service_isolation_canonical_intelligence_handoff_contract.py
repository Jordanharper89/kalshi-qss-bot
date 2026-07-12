"""
OLA-020
Oracle Service Isolation and Canonical Intelligence Handoff Contract

Canonical company boundary between Oracle and Q Series.

Architecture:

ORACLE SERVICE
    |
READ-ONLY INTELLIGENCE
    |
CANONICAL MARKET IDENTITY
VERIFIED VENUE IDENTITY
EXPLICIT VALIDITY / EXPIRATION
ORACLE EVIDENCE IDENTITY
REPLAY IDENTITY
    |
OLA-020 IMMUTABLE HANDOFF RECORD
    |
Q SERIES INTAKE SERVICE
    |
INDEPENDENT Q SERIES VALIDATION
AUTHORIZATION
EXECUTION

Important ownership rules:

Oracle owns:
- observation
- normalization
- analysis
- discovery
- memory
- replay
- explanation
- canonical intelligence publication

Q Series owns:
- intake validation
- venue reconciliation
- execution-adapter resolution
- trade authorization
- order placement
- fill confirmation
- position-state mutation
- capital movement

Oracle and Q Series must not share execution authority.

The handoff record is immutable evidence.

OLA-020 does not:
- authorize a trade
- resolve an execution adapter
- invoke an execution adapter
- place an order
- confirm a fill
- move funds
- mutate a portfolio
- mutate Q Series state
- mutate Oracle history
- start a service
- start polling
- call Kalshi
- invoke OLA-017

All timestamps are caller supplied.

Canonical stable JSON hashing is required.

repr() is never used.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from typing import Any, Mapping


SCHEMA_VERSION = "OLA-020"
ENGINE_ID = "OLA-020"

ORACLE_SERVICE_ROLE = "oracle_read_only_intelligence"
Q_SERIES_SERVICE_ROLE = "qseries_authorization_execution"

HANDOFF_STATUS_PUBLISHED = "published"

SUPPORTED_HANDOFF_STATUSES = (
    HANDOFF_STATUS_PUBLISHED,
)

HANDOFF_RECORD_TYPE = (
    "oracle_canonical_intelligence_handoff_record"
)

SERVICE_ISOLATION_RECORD_TYPE = (
    "oracle_qseries_service_isolation_contract"
)


class OracleServiceIsolationContractError(ValueError):
    """Raised when the service-isolation contract is malformed."""


class CanonicalIntelligenceHandoffContractError(ValueError):
    """Raised when canonical handoff data is malformed."""


class CanonicalIntelligenceHandoffInvariantError(RuntimeError):
    """Raised when permanent Oracle/Q Series invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise CanonicalIntelligenceHandoffContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise CanonicalIntelligenceHandoffContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_bool(
    value: Any,
    field_name: str,
) -> bool:
    if not isinstance(value, bool):
        raise CanonicalIntelligenceHandoffContractError(
            f"{field_name} must be bool"
        )

    return value


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise CanonicalIntelligenceHandoffContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise CanonicalIntelligenceHandoffContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _canonicalize(
    value: Any,
) -> Any:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise CanonicalIntelligenceHandoffContractError(
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
        result = {}

        for key in sorted(value):
            if not isinstance(key, str):
                raise CanonicalIntelligenceHandoffContractError(
                    "canonical mapping keys must be strings"
                )

            result[key] = _canonicalize(
                value[key]
            )

        return result

    if isinstance(value, (list, tuple)):
        return [
            _canonicalize(item)
            for item in value
        ]

    raise CanonicalIntelligenceHandoffContractError(
        "unsupported canonical value type: "
        f"{type(value).__name__}"
    )


def canonical_json(
    value: Any,
) -> str:
    return json.dumps(
        _canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def stable_hash(
    value: Any,
) -> str:
    return sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def _immutable_mapping(
    value: Mapping[str, Any],
    field_name: str,
) -> tuple[tuple[str, Any], ...]:
    if not isinstance(value, Mapping):
        raise CanonicalIntelligenceHandoffContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(value)

    if not isinstance(canonical, dict):
        raise CanonicalIntelligenceHandoffContractError(
            f"{field_name} must canonicalize to a mapping"
        )

    forbidden_keys = {
        "password",
        "passwd",
        "secret",
        "api_key",
        "private_key",
        "signing_key",
        "dsn",
        "database_url",
        "connection_string",
    }

    result = tuple(
        (
            key,
            canonical[key],
        )
        for key in sorted(canonical)
    )

    for key, _ in result:
        if key.strip().lower() in forbidden_keys:
            raise CanonicalIntelligenceHandoffContractError(
                f"{field_name} contains forbidden "
                f"secret-bearing key: {key}"
            )

    return result


def _mapping_from_immutable(
    value: tuple[tuple[str, Any], ...],
) -> dict[str, Any]:
    return {
        key: item
        for key, item in value
    }


def _validate_hash(
    value: Any,
    field_name: str,
) -> str:
    normalized = _require_non_empty_string(
        value,
        field_name,
    )

    if len(normalized) != 64:
        raise CanonicalIntelligenceHandoffContractError(
            f"{field_name} must be a 64-character hash"
        )

    try:
        int(
            normalized,
            16,
        )

    except ValueError as exc:
        raise CanonicalIntelligenceHandoffContractError(
            f"{field_name} must be hexadecimal"
        ) from exc

    return normalized.lower()


@dataclass(frozen=True, slots=True)
class OracleQSeriesServiceIsolationContract:
    schema_version: str
    engine_id: str
    contract_id: str
    oracle_service_id: str
    oracle_service_role: str
    qseries_service_id: str
    qseries_service_role: str
    separate_process_required: bool
    direct_execution_import_allowed: bool
    oracle_execution_authority: bool
    qseries_oracle_history_mutation_allowed: bool
    immutable_handoff_required: bool
    durable_handoff_boundary_required: bool
    independent_qseries_validation_required: bool
    contract_metadata: tuple[
        tuple[str, Any],
        ...
    ]
    contract_hash: str
    immutable: bool
    replayable: bool
    auditable: bool
    explainable: bool
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    @classmethod
    def create(
        cls,
        *,
        contract_id: str,
        oracle_service_id: str,
        qseries_service_id: str,
        contract_metadata: Mapping[str, Any],
    ) -> "OracleQSeriesServiceIsolationContract":
        normalized_contract_id = _require_non_empty_string(
            contract_id,
            "contract_id",
        )

        normalized_oracle_service_id = _require_non_empty_string(
            oracle_service_id,
            "oracle_service_id",
        )

        normalized_qseries_service_id = _require_non_empty_string(
            qseries_service_id,
            "qseries_service_id",
        )

        if (
            normalized_oracle_service_id
            == normalized_qseries_service_id
        ):
            raise OracleServiceIsolationContractError(
                "Oracle and Q Series service identities "
                "must be different"
            )

        immutable_metadata = _immutable_mapping(
            contract_metadata,
            "contract_metadata",
        )

        provisional = cls(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            contract_id=normalized_contract_id,
            oracle_service_id=normalized_oracle_service_id,
            oracle_service_role=ORACLE_SERVICE_ROLE,
            qseries_service_id=normalized_qseries_service_id,
            qseries_service_role=Q_SERIES_SERVICE_ROLE,
            separate_process_required=True,
            direct_execution_import_allowed=False,
            oracle_execution_authority=False,
            qseries_oracle_history_mutation_allowed=False,
            immutable_handoff_required=True,
            durable_handoff_boundary_required=True,
            independent_qseries_validation_required=True,
            contract_metadata=immutable_metadata,
            contract_hash="",
            immutable=True,
            replayable=True,
            auditable=True,
            explainable=True,
            read_only=True,
            execution_allowed=False,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

        contract_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": SERVICE_ISOLATION_RECORD_TYPE,
                "contract": provisional.to_canonical_dict(
                    include_contract_hash=False
                ),
            }
        )

        return cls(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            contract_id=provisional.contract_id,
            oracle_service_id=provisional.oracle_service_id,
            oracle_service_role=provisional.oracle_service_role,
            qseries_service_id=provisional.qseries_service_id,
            qseries_service_role=provisional.qseries_service_role,
            separate_process_required=True,
            direct_execution_import_allowed=False,
            oracle_execution_authority=False,
            qseries_oracle_history_mutation_allowed=False,
            immutable_handoff_required=True,
            durable_handoff_boundary_required=True,
            independent_qseries_validation_required=True,
            contract_metadata=provisional.contract_metadata,
            contract_hash=contract_hash,
            immutable=True,
            replayable=True,
            auditable=True,
            explainable=True,
            read_only=True,
            execution_allowed=False,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

    def to_canonical_dict(
        self,
        *,
        include_contract_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "contract_id": self.contract_id,
            "oracle_service_id": self.oracle_service_id,
            "oracle_service_role": self.oracle_service_role,
            "qseries_service_id": self.qseries_service_id,
            "qseries_service_role": self.qseries_service_role,
            "separate_process_required": (
                self.separate_process_required
            ),
            "direct_execution_import_allowed": (
                self.direct_execution_import_allowed
            ),
            "oracle_execution_authority": (
                self.oracle_execution_authority
            ),
            "qseries_oracle_history_mutation_allowed": (
                self.qseries_oracle_history_mutation_allowed
            ),
            "immutable_handoff_required": (
                self.immutable_handoff_required
            ),
            "durable_handoff_boundary_required": (
                self.durable_handoff_boundary_required
            ),
            "independent_qseries_validation_required": (
                self.independent_qseries_validation_required
            ),
            "contract_metadata": _mapping_from_immutable(
                self.contract_metadata
            ),
            "immutable": self.immutable,
            "replayable": self.replayable,
            "auditable": self.auditable,
            "explainable": self.explainable,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_adapter_resolved": (
                self.execution_adapter_resolved
            ),
            "execution_adapter_invoked": (
                self.execution_adapter_invoked
            ),
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }

        if include_contract_hash:
            result["contract_hash"] = self.contract_hash

        return result


@dataclass(frozen=True, slots=True)
class CanonicalIntelligenceHandoffRecord:
    schema_version: str
    engine_id: str
    handoff_id: str
    handoff_status: str
    service_contract_id: str
    service_contract_hash: str
    oracle_service_id: str
    qseries_service_id: str
    opportunity_id: str
    thesis_id: str
    canonical_market_id: str
    source_market_id: str
    venue_id: str
    venue_name: str
    venue_type: str
    venue_verified: bool
    opportunity_type: str
    instrument_type: str
    expression_type: str
    direction: str
    reference_price: str
    price_unit: str
    valid_from: datetime
    expires_at: datetime
    intelligence_generated_at: datetime
    published_at: datetime
    oracle_evidence_hash: str
    replay_reference_id: str
    replay_evidence_hash: str
    source_record_id: str
    source_record_hash: str
    independent_qseries_validation_required: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool
    handoff_metadata: tuple[
        tuple[str, Any],
        ...
    ]
    handoff_hash: str
    immutable: bool
    replayable: bool
    auditable: bool
    explainable: bool
    read_only: bool
    execution_allowed: bool

    @classmethod
    def create(
        cls,
        *,
        service_contract: OracleQSeriesServiceIsolationContract,
        opportunity_id: str,
        thesis_id: str,
        canonical_market_id: str,
        source_market_id: str,
        venue_id: str,
        venue_name: str,
        venue_type: str,
        venue_verified: bool,
        opportunity_type: str,
        instrument_type: str,
        expression_type: str,
        direction: str,
        reference_price: str,
        price_unit: str,
        valid_from: datetime,
        expires_at: datetime,
        intelligence_generated_at: datetime,
        published_at: datetime,
        oracle_evidence_hash: str,
        replay_reference_id: str,
        replay_evidence_hash: str,
        source_record_id: str,
        source_record_hash: str,
        handoff_metadata: Mapping[str, Any],
    ) -> "CanonicalIntelligenceHandoffRecord":
        if not isinstance(
            service_contract,
            OracleQSeriesServiceIsolationContract,
        ):
            raise CanonicalIntelligenceHandoffContractError(
                "service_contract must be "
                "OracleQSeriesServiceIsolationContract"
            )

        cls._validate_service_contract(
            service_contract
        )

        normalized_opportunity_id = _require_non_empty_string(
            opportunity_id,
            "opportunity_id",
        )

        normalized_thesis_id = _require_non_empty_string(
            thesis_id,
            "thesis_id",
        )

        normalized_canonical_market_id = _require_non_empty_string(
            canonical_market_id,
            "canonical_market_id",
        )

        if not normalized_canonical_market_id.startswith(
            "market."
        ):
            raise CanonicalIntelligenceHandoffContractError(
                "canonical_market_id must use market. identity"
            )

        normalized_source_market_id = _require_non_empty_string(
            source_market_id,
            "source_market_id",
        )

        normalized_venue_id = _require_non_empty_string(
            venue_id,
            "venue_id",
        )

        if not normalized_venue_id.startswith(
            "venue."
        ):
            raise CanonicalIntelligenceHandoffContractError(
                "venue_id must use venue. identity"
            )

        normalized_venue_name = _require_non_empty_string(
            venue_name,
            "venue_name",
        )

        normalized_venue_type = _require_non_empty_string(
            venue_type,
            "venue_type",
        )

        normalized_venue_verified = _require_bool(
            venue_verified,
            "venue_verified",
        )

        if normalized_venue_verified is not True:
            raise CanonicalIntelligenceHandoffContractError(
                "unverified venue cannot enter canonical handoff"
            )

        normalized_opportunity_type = _require_non_empty_string(
            opportunity_type,
            "opportunity_type",
        )

        normalized_instrument_type = _require_non_empty_string(
            instrument_type,
            "instrument_type",
        )

        normalized_expression_type = _require_non_empty_string(
            expression_type,
            "expression_type",
        )

        normalized_direction = _require_non_empty_string(
            direction,
            "direction",
        )

        normalized_reference_price = _require_non_empty_string(
            reference_price,
            "reference_price",
        )

        normalized_price_unit = _require_non_empty_string(
            price_unit,
            "price_unit",
        )

        normalized_valid_from = _require_aware_datetime(
            valid_from,
            "valid_from",
        )

        normalized_expires_at = _require_aware_datetime(
            expires_at,
            "expires_at",
        )

        normalized_intelligence_generated_at = (
            _require_aware_datetime(
                intelligence_generated_at,
                "intelligence_generated_at",
            )
        )

        normalized_published_at = _require_aware_datetime(
            published_at,
            "published_at",
        )

        if normalized_expires_at <= normalized_valid_from:
            raise CanonicalIntelligenceHandoffContractError(
                "expires_at must be after valid_from"
            )

        if (
            normalized_intelligence_generated_at
            > normalized_published_at
        ):
            raise CanonicalIntelligenceHandoffContractError(
                "published_at cannot precede "
                "intelligence_generated_at"
            )

        if normalized_published_at < normalized_valid_from:
            raise CanonicalIntelligenceHandoffContractError(
                "published_at cannot precede valid_from"
            )

        if normalized_published_at >= normalized_expires_at:
            raise CanonicalIntelligenceHandoffContractError(
                "expired intelligence cannot enter canonical handoff"
            )

        normalized_oracle_evidence_hash = _validate_hash(
            oracle_evidence_hash,
            "oracle_evidence_hash",
        )

        normalized_replay_reference_id = _require_non_empty_string(
            replay_reference_id,
            "replay_reference_id",
        )

        normalized_replay_evidence_hash = _validate_hash(
            replay_evidence_hash,
            "replay_evidence_hash",
        )

        normalized_source_record_id = _require_non_empty_string(
            source_record_id,
            "source_record_id",
        )

        normalized_source_record_hash = _validate_hash(
            source_record_hash,
            "source_record_hash",
        )

        immutable_metadata = _immutable_mapping(
            handoff_metadata,
            "handoff_metadata",
        )

        handoff_identity_payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "canonical_intelligence_handoff_identity",
            "service_contract_hash": service_contract.contract_hash,
            "oracle_service_id": service_contract.oracle_service_id,
            "qseries_service_id": service_contract.qseries_service_id,
            "opportunity_id": normalized_opportunity_id,
            "thesis_id": normalized_thesis_id,
            "canonical_market_id": normalized_canonical_market_id,
            "venue_id": normalized_venue_id,
            "valid_from": normalized_valid_from,
            "expires_at": normalized_expires_at,
            "oracle_evidence_hash": normalized_oracle_evidence_hash,
            "replay_evidence_hash": normalized_replay_evidence_hash,
            "source_record_hash": normalized_source_record_hash,
        }

        handoff_id = "handoff." + stable_hash(
            handoff_identity_payload
        )

        provisional = cls(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            handoff_id=handoff_id,
            handoff_status=HANDOFF_STATUS_PUBLISHED,
            service_contract_id=service_contract.contract_id,
            service_contract_hash=service_contract.contract_hash,
            oracle_service_id=service_contract.oracle_service_id,
            qseries_service_id=service_contract.qseries_service_id,
            opportunity_id=normalized_opportunity_id,
            thesis_id=normalized_thesis_id,
            canonical_market_id=normalized_canonical_market_id,
            source_market_id=normalized_source_market_id,
            venue_id=normalized_venue_id,
            venue_name=normalized_venue_name,
            venue_type=normalized_venue_type,
            venue_verified=True,
            opportunity_type=normalized_opportunity_type,
            instrument_type=normalized_instrument_type,
            expression_type=normalized_expression_type,
            direction=normalized_direction,
            reference_price=normalized_reference_price,
            price_unit=normalized_price_unit,
            valid_from=normalized_valid_from,
            expires_at=normalized_expires_at,
            intelligence_generated_at=(
                normalized_intelligence_generated_at
            ),
            published_at=normalized_published_at,
            oracle_evidence_hash=normalized_oracle_evidence_hash,
            replay_reference_id=normalized_replay_reference_id,
            replay_evidence_hash=normalized_replay_evidence_hash,
            source_record_id=normalized_source_record_id,
            source_record_hash=normalized_source_record_hash,
            independent_qseries_validation_required=True,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
            handoff_metadata=immutable_metadata,
            handoff_hash="",
            immutable=True,
            replayable=True,
            auditable=True,
            explainable=True,
            read_only=True,
            execution_allowed=False,
        )

        handoff_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": HANDOFF_RECORD_TYPE,
                "handoff": provisional.to_canonical_dict(
                    include_handoff_hash=False
                ),
            }
        )

        return cls(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            handoff_id=provisional.handoff_id,
            handoff_status=provisional.handoff_status,
            service_contract_id=provisional.service_contract_id,
            service_contract_hash=provisional.service_contract_hash,
            oracle_service_id=provisional.oracle_service_id,
            qseries_service_id=provisional.qseries_service_id,
            opportunity_id=provisional.opportunity_id,
            thesis_id=provisional.thesis_id,
            canonical_market_id=provisional.canonical_market_id,
            source_market_id=provisional.source_market_id,
            venue_id=provisional.venue_id,
            venue_name=provisional.venue_name,
            venue_type=provisional.venue_type,
            venue_verified=True,
            opportunity_type=provisional.opportunity_type,
            instrument_type=provisional.instrument_type,
            expression_type=provisional.expression_type,
            direction=provisional.direction,
            reference_price=provisional.reference_price,
            price_unit=provisional.price_unit,
            valid_from=provisional.valid_from,
            expires_at=provisional.expires_at,
            intelligence_generated_at=(
                provisional.intelligence_generated_at
            ),
            published_at=provisional.published_at,
            oracle_evidence_hash=provisional.oracle_evidence_hash,
            replay_reference_id=provisional.replay_reference_id,
            replay_evidence_hash=provisional.replay_evidence_hash,
            source_record_id=provisional.source_record_id,
            source_record_hash=provisional.source_record_hash,
            independent_qseries_validation_required=True,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
            handoff_metadata=provisional.handoff_metadata,
            handoff_hash=handoff_hash,
            immutable=True,
            replayable=True,
            auditable=True,
            explainable=True,
            read_only=True,
            execution_allowed=False,
        )

    @staticmethod
    def _validate_service_contract(
        service_contract: OracleQSeriesServiceIsolationContract,
    ) -> None:
        expected_true = {
            "separate_process_required": (
                service_contract.separate_process_required
            ),
            "immutable_handoff_required": (
                service_contract.immutable_handoff_required
            ),
            "durable_handoff_boundary_required": (
                service_contract.durable_handoff_boundary_required
            ),
            "independent_qseries_validation_required": (
                service_contract.independent_qseries_validation_required
            ),
            "immutable": service_contract.immutable,
            "replayable": service_contract.replayable,
            "auditable": service_contract.auditable,
            "explainable": service_contract.explainable,
            "read_only": service_contract.read_only,
        }

        if not all(expected_true.values()):
            raise CanonicalIntelligenceHandoffInvariantError(
                "service-isolation positive invariants violated"
            )

        expected_false = {
            "direct_execution_import_allowed": (
                service_contract.direct_execution_import_allowed
            ),
            "oracle_execution_authority": (
                service_contract.oracle_execution_authority
            ),
            "qseries_oracle_history_mutation_allowed": (
                service_contract.qseries_oracle_history_mutation_allowed
            ),
            "execution_allowed": service_contract.execution_allowed,
            "execution_adapter_resolved": (
                service_contract.execution_adapter_resolved
            ),
            "execution_adapter_invoked": (
                service_contract.execution_adapter_invoked
            ),
            "trade_authorization_allowed": (
                service_contract.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                service_contract.order_placement_allowed
            ),
            "funds_moved": service_contract.funds_moved,
            "portfolio_mutated": service_contract.portfolio_mutated,
        }

        if any(expected_false.values()):
            raise CanonicalIntelligenceHandoffInvariantError(
                "service-isolation no-execution invariants violated"
            )

    def to_canonical_dict(
        self,
        *,
        include_handoff_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "handoff_id": self.handoff_id,
            "handoff_status": self.handoff_status,
            "service_contract_id": self.service_contract_id,
            "service_contract_hash": self.service_contract_hash,
            "oracle_service_id": self.oracle_service_id,
            "qseries_service_id": self.qseries_service_id,
            "opportunity_id": self.opportunity_id,
            "thesis_id": self.thesis_id,
            "canonical_market_id": self.canonical_market_id,
            "source_market_id": self.source_market_id,
            "venue_id": self.venue_id,
            "venue_name": self.venue_name,
            "venue_type": self.venue_type,
            "venue_verified": self.venue_verified,
            "opportunity_type": self.opportunity_type,
            "instrument_type": self.instrument_type,
            "expression_type": self.expression_type,
            "direction": self.direction,
            "reference_price": self.reference_price,
            "price_unit": self.price_unit,
            "valid_from": self.valid_from.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "intelligence_generated_at": (
                self.intelligence_generated_at.isoformat()
            ),
            "published_at": self.published_at.isoformat(),
            "oracle_evidence_hash": self.oracle_evidence_hash,
            "replay_reference_id": self.replay_reference_id,
            "replay_evidence_hash": self.replay_evidence_hash,
            "source_record_id": self.source_record_id,
            "source_record_hash": self.source_record_hash,
            "independent_qseries_validation_required": (
                self.independent_qseries_validation_required
            ),
            "execution_adapter_resolved": (
                self.execution_adapter_resolved
            ),
            "execution_adapter_invoked": (
                self.execution_adapter_invoked
            ),
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
            "handoff_metadata": _mapping_from_immutable(
                self.handoff_metadata
            ),
            "immutable": self.immutable,
            "replayable": self.replayable,
            "auditable": self.auditable,
            "explainable": self.explainable,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
        }

        if include_handoff_hash:
            result["handoff_hash"] = self.handoff_hash

        return result

    def verify_handoff_hash(
        self,
    ) -> bool:
        expected = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": HANDOFF_RECORD_TYPE,
                "handoff": self.to_canonical_dict(
                    include_handoff_hash=False
                ),
            }
        )

        return self.handoff_hash == expected


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "ORACLE_SERVICE_ROLE",
    "Q_SERIES_SERVICE_ROLE",
    "HANDOFF_STATUS_PUBLISHED",
    "SUPPORTED_HANDOFF_STATUSES",
    "OracleServiceIsolationContractError",
    "CanonicalIntelligenceHandoffContractError",
    "CanonicalIntelligenceHandoffInvariantError",
    "OracleQSeriesServiceIsolationContract",
    "CanonicalIntelligenceHandoffRecord",
    "canonical_json",
    "stable_hash",
]
