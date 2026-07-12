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
    / "oracle_service_isolation_canonical_intelligence_handoff_contract.py"
)

PACKAGE_INIT_PATH = PACKAGE_DIR / "__init__.py"

TEST_PATH = (
    ROOT
    / "test_ola_020_oracle_service_isolation_canonical_intelligence_handoff_contract.py"
)


MODULE_CONTENT = r'''
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
'''


TEST_CONTENT = r'''
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone


from qseries_v2.oracle_intelligence.live_acquisition.oracle_service_isolation_canonical_intelligence_handoff_contract import (
    CanonicalIntelligenceHandoffContractError,
    CanonicalIntelligenceHandoffRecord,
    OracleQSeriesServiceIsolationContract,
    OracleServiceIsolationContractError,
)


VALID_FROM = datetime(
    2026,
    7,
    12,
    15,
    0,
    0,
    tzinfo=timezone.utc,
)

INTELLIGENCE_GENERATED_AT = datetime(
    2026,
    7,
    12,
    15,
    0,
    2,
    tzinfo=timezone.utc,
)

PUBLISHED_AT = datetime(
    2026,
    7,
    12,
    15,
    0,
    5,
    tzinfo=timezone.utc,
)

EXPIRES_AT = datetime(
    2026,
    7,
    12,
    15,
    15,
    0,
    tzinfo=timezone.utc,
)


def build_service_contract():
    return OracleQSeriesServiceIsolationContract.create(
        contract_id=(
            "oracle.qseries.service_isolation.v1"
        ),
        oracle_service_id=(
            "service.oracle.intelligence"
        ),
        qseries_service_id=(
            "service.qseries.execution"
        ),
        contract_metadata={
            "environment": "production",
            "handoff_transport": "durable_boundary",
            "oracle_process": "separate",
            "qseries_process": "separate",
        },
    )


def build_handoff():
    return CanonicalIntelligenceHandoffRecord.create(
        service_contract=build_service_contract(),
        opportunity_id=(
            "opportunity.kalshi.btc.ola020.001"
        ),
        thesis_id=(
            "thesis.btc.bearish.ola020.001"
        ),
        canonical_market_id=(
            "market."
            "95b13d7489267bf051b0173a27c3e98b"
            "155473362c6ca4e47431a16e623044ab"
        ),
        source_market_id=(
            "KXBTC-26JUL12-116000"
        ),
        venue_id="venue.kalshi",
        venue_name="Kalshi",
        venue_type="prediction_market",
        venue_verified=True,
        opportunity_type="prediction_market",
        instrument_type="prediction_contract",
        expression_type="buy_yes",
        direction="bearish",
        reference_price="0.31",
        price_unit="USD_PER_SHARE",
        valid_from=VALID_FROM,
        expires_at=EXPIRES_AT,
        intelligence_generated_at=(
            INTELLIGENCE_GENERATED_AT
        ),
        published_at=PUBLISHED_AT,
        oracle_evidence_hash=(
            "a" * 64
        ),
        replay_reference_id=(
            "replay.oracle.ola020.001"
        ),
        replay_evidence_hash=(
            "b" * 64
        ),
        source_record_id=(
            "observation.kalshi.ola020.001"
        ),
        source_record_hash=(
            "c" * 64
        ),
        handoff_metadata={
            "publisher": "oracle",
            "consumer": "qseries",
            "historical_oi_handoff_replaced": False,
            "modern_canonical_boundary": True,
        },
    )


def run_service_isolation_contract_test():
    contract = build_service_contract()

    assert contract.schema_version == "OLA-020"

    assert contract.engine_id == "OLA-020"

    assert contract.contract_id == (
        "oracle.qseries.service_isolation.v1"
    )

    assert contract.oracle_service_id == (
        "service.oracle.intelligence"
    )

    assert contract.oracle_service_role == (
        "oracle_read_only_intelligence"
    )

    assert contract.qseries_service_id == (
        "service.qseries.execution"
    )

    assert contract.qseries_service_role == (
        "qseries_authorization_execution"
    )

    assert contract.separate_process_required is True

    assert (
        contract.direct_execution_import_allowed
        is False
    )

    assert contract.oracle_execution_authority is False

    assert (
        contract.qseries_oracle_history_mutation_allowed
        is False
    )

    assert contract.immutable_handoff_required is True

    assert (
        contract.durable_handoff_boundary_required
        is True
    )

    assert (
        contract.independent_qseries_validation_required
        is True
    )

    assert len(contract.contract_hash) == 64

    assert contract.immutable is True
    assert contract.replayable is True
    assert contract.auditable is True
    assert contract.explainable is True
    assert contract.read_only is True

    assert contract.execution_allowed is False

    assert contract.execution_adapter_resolved is False

    assert contract.execution_adapter_invoked is False

    assert contract.trade_authorization_allowed is False

    assert contract.order_placement_allowed is False

    assert contract.funds_moved is False

    assert contract.portfolio_mutated is False

    try:
        contract.oracle_execution_authority = True

        raise AssertionError(
            "service contract must be immutable"
        )

    except FrozenInstanceError:
        pass

    return contract


def run_canonical_handoff_test():
    handoff = build_handoff()

    assert handoff.schema_version == "OLA-020"

    assert handoff.engine_id == "OLA-020"

    assert handoff.handoff_id.startswith(
        "handoff."
    )

    assert handoff.handoff_status == "published"

    assert handoff.service_contract_id == (
        "oracle.qseries.service_isolation.v1"
    )

    assert len(handoff.service_contract_hash) == 64

    assert handoff.oracle_service_id == (
        "service.oracle.intelligence"
    )

    assert handoff.qseries_service_id == (
        "service.qseries.execution"
    )

    assert handoff.opportunity_id == (
        "opportunity.kalshi.btc.ola020.001"
    )

    assert handoff.thesis_id == (
        "thesis.btc.bearish.ola020.001"
    )

    assert handoff.canonical_market_id.startswith(
        "market."
    )

    assert handoff.source_market_id == (
        "KXBTC-26JUL12-116000"
    )

    assert handoff.venue_id == "venue.kalshi"

    assert handoff.venue_name == "Kalshi"

    assert handoff.venue_type == "prediction_market"

    assert handoff.venue_verified is True

    assert handoff.opportunity_type == (
        "prediction_market"
    )

    assert handoff.instrument_type == (
        "prediction_contract"
    )

    assert handoff.expression_type == "buy_yes"

    assert handoff.direction == "bearish"

    assert handoff.reference_price == "0.31"

    assert handoff.price_unit == "USD_PER_SHARE"

    assert handoff.valid_from == VALID_FROM

    assert handoff.expires_at == EXPIRES_AT

    assert (
        handoff.intelligence_generated_at
        == INTELLIGENCE_GENERATED_AT
    )

    assert handoff.published_at == PUBLISHED_AT

    assert len(handoff.oracle_evidence_hash) == 64

    assert handoff.replay_reference_id == (
        "replay.oracle.ola020.001"
    )

    assert len(handoff.replay_evidence_hash) == 64

    assert handoff.source_record_id == (
        "observation.kalshi.ola020.001"
    )

    assert len(handoff.source_record_hash) == 64

    assert (
        handoff.independent_qseries_validation_required
        is True
    )

    assert handoff.execution_adapter_resolved is False

    assert handoff.execution_adapter_invoked is False

    assert handoff.trade_authorization_allowed is False

    assert handoff.order_placement_allowed is False

    assert handoff.funds_moved is False

    assert handoff.portfolio_mutated is False

    assert handoff.immutable is True
    assert handoff.replayable is True
    assert handoff.auditable is True
    assert handoff.explainable is True
    assert handoff.read_only is True

    assert handoff.execution_allowed is False

    assert len(handoff.handoff_hash) == 64

    assert handoff.verify_handoff_hash() is True

    try:
        handoff.reference_price = "0.99"

        raise AssertionError(
            "handoff record must be immutable"
        )

    except FrozenInstanceError:
        pass

    return handoff


def run_deterministic_replay_test():
    first = build_handoff()

    second = build_handoff()

    assert first == second

    assert first.handoff_id == second.handoff_id

    assert first.handoff_hash == second.handoff_hash

    assert first.verify_handoff_hash() is True

    assert second.verify_handoff_hash() is True


def run_fail_closed_tests():
    try:
        OracleQSeriesServiceIsolationContract.create(
            contract_id="invalid.same.service",
            oracle_service_id="service.shared",
            qseries_service_id="service.shared",
            contract_metadata={},
        )

        raise AssertionError(
            "shared Oracle/Q Series service identity "
            "must fail closed"
        )

    except OracleServiceIsolationContractError:
        pass

    base = {
        "service_contract": build_service_contract(),
        "opportunity_id": "opportunity.test",
        "thesis_id": "thesis.test",
        "canonical_market_id": "market.test",
        "source_market_id": "source-market-test",
        "venue_id": "venue.kalshi",
        "venue_name": "Kalshi",
        "venue_type": "prediction_market",
        "venue_verified": True,
        "opportunity_type": "prediction_market",
        "instrument_type": "prediction_contract",
        "expression_type": "buy_yes",
        "direction": "bearish",
        "reference_price": "0.31",
        "price_unit": "USD_PER_SHARE",
        "valid_from": VALID_FROM,
        "expires_at": EXPIRES_AT,
        "intelligence_generated_at": (
            INTELLIGENCE_GENERATED_AT
        ),
        "published_at": PUBLISHED_AT,
        "oracle_evidence_hash": "a" * 64,
        "replay_reference_id": "replay.test",
        "replay_evidence_hash": "b" * 64,
        "source_record_id": "observation.test",
        "source_record_hash": "c" * 64,
        "handoff_metadata": {},
    }

    invalid_venue = dict(base)

    invalid_venue["venue_verified"] = False

    try:
        CanonicalIntelligenceHandoffRecord.create(
            **invalid_venue
        )

        raise AssertionError(
            "unverified venue must fail closed"
        )

    except CanonicalIntelligenceHandoffContractError:
        pass

    expired = dict(base)

    expired["published_at"] = EXPIRES_AT

    try:
        CanonicalIntelligenceHandoffRecord.create(
            **expired
        )

        raise AssertionError(
            "expired handoff must fail closed"
        )

    except CanonicalIntelligenceHandoffContractError:
        pass

    naive_time = dict(base)

    naive_time["valid_from"] = datetime(
        2026,
        7,
        12,
        15,
        0,
        0,
    )

    try:
        CanonicalIntelligenceHandoffRecord.create(
            **naive_time
        )

        raise AssertionError(
            "naive contract timestamp must fail closed"
        )

    except CanonicalIntelligenceHandoffContractError:
        pass

    invalid_hash = dict(base)

    invalid_hash["oracle_evidence_hash"] = "not-a-hash"

    try:
        CanonicalIntelligenceHandoffRecord.create(
            **invalid_hash
        )

        raise AssertionError(
            "invalid evidence hash must fail closed"
        )

    except CanonicalIntelligenceHandoffContractError:
        pass

    secret_metadata = dict(base)

    secret_metadata["handoff_metadata"] = {
        "api_key": "must-not-enter-handoff"
    }

    try:
        CanonicalIntelligenceHandoffRecord.create(
            **secret_metadata
        )

        raise AssertionError(
            "secret-bearing metadata must fail closed"
        )

    except CanonicalIntelligenceHandoffContractError:
        pass


def main():
    contract = run_service_isolation_contract_test()

    handoff = run_canonical_handoff_test()

    run_deterministic_replay_test()

    run_fail_closed_tests()

    result = {
        "schema_version": handoff.schema_version,
        "engine_id": handoff.engine_id,
        "status": "passed",
        "contract_id": contract.contract_id,
        "oracle_service_id": (
            contract.oracle_service_id
        ),
        "oracle_service_role": (
            contract.oracle_service_role
        ),
        "qseries_service_id": (
            contract.qseries_service_id
        ),
        "qseries_service_role": (
            contract.qseries_service_role
        ),
        "separate_process_required": (
            contract.separate_process_required
        ),
        "direct_execution_import_allowed": (
            contract.direct_execution_import_allowed
        ),
        "oracle_execution_authority": (
            contract.oracle_execution_authority
        ),
        "qseries_oracle_history_mutation_allowed": (
            contract.qseries_oracle_history_mutation_allowed
        ),
        "immutable_handoff_required": (
            contract.immutable_handoff_required
        ),
        "durable_handoff_boundary_required": (
            contract.durable_handoff_boundary_required
        ),
        "independent_qseries_validation_required": (
            handoff.independent_qseries_validation_required
        ),
        "handoff_status": handoff.handoff_status,
        "canonical_market_id": (
            handoff.canonical_market_id
        ),
        "source_market_id": handoff.source_market_id,
        "venue_id": handoff.venue_id,
        "venue_name": handoff.venue_name,
        "venue_verified": handoff.venue_verified,
        "opportunity_type": handoff.opportunity_type,
        "instrument_type": handoff.instrument_type,
        "expression_type": handoff.expression_type,
        "direction": handoff.direction,
        "reference_price": handoff.reference_price,
        "price_unit": handoff.price_unit,
        "explicit_valid_from": (
            handoff.valid_from.isoformat()
        ),
        "explicit_expires_at": (
            handoff.expires_at.isoformat()
        ),
        "oracle_evidence_hash_preserved": True,
        "replay_reference_preserved": True,
        "source_record_identity_preserved": True,
        "deterministic_handoff_hashing": True,
        "unverified_venue_blocked": True,
        "expired_handoff_blocked": True,
        "naive_timestamp_blocked": True,
        "invalid_evidence_hash_blocked": True,
        "secret_metadata_blocked": True,
        "execution_adapter_resolved": (
            handoff.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            handoff.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            handoff.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            handoff.order_placement_allowed
        ),
        "funds_moved": handoff.funds_moved,
        "portfolio_mutated": handoff.portfolio_mutated,
        "read_only": handoff.read_only,
        "execution_allowed": handoff.execution_allowed,
    }

    print(
        "[PASS] OLA-020 Oracle Service Isolation and "
        "Canonical Intelligence Handoff Contract"
    )

    print(result)


if __name__ == "__main__":
    main()
'''


EXPORT_BLOCK = r'''

from .oracle_service_isolation_canonical_intelligence_handoff_contract import (
    HANDOFF_STATUS_PUBLISHED,
    ORACLE_SERVICE_ROLE,
    Q_SERIES_SERVICE_ROLE,
    CanonicalIntelligenceHandoffContractError,
    CanonicalIntelligenceHandoffInvariantError,
    CanonicalIntelligenceHandoffRecord,
    OracleQSeriesServiceIsolationContract,
    OracleServiceIsolationContractError,
)
'''


EXPORT_NAMES = [
    "HANDOFF_STATUS_PUBLISHED",
    "ORACLE_SERVICE_ROLE",
    "Q_SERIES_SERVICE_ROLE",
    "CanonicalIntelligenceHandoffContractError",
    "CanonicalIntelligenceHandoffInvariantError",
    "CanonicalIntelligenceHandoffRecord",
    "OracleQSeriesServiceIsolationContract",
    "OracleServiceIsolationContractError",
]


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


def update_package_exports() -> None:
    existing = PACKAGE_INIT_PATH.read_text(
        encoding="utf-8"
    )

    import_marker = (
        "from .oracle_service_isolation_canonical_"
        "intelligence_handoff_contract import"
    )

    updated = existing

    if import_marker not in updated:
        updated = (
            updated.rstrip()
            + "\n"
            + textwrap.dedent(EXPORT_BLOCK)
        )

    all_start = updated.find("__all__ = [")

    if all_start == -1:
        raise RuntimeError(
            "__init__.py does not contain __all__"
        )

    closing_index = updated.find(
        "]",
        all_start,
    )

    if closing_index == -1:
        raise RuntimeError(
            "__init__.py does not contain "
            "__all__ closing bracket"
        )

    for name in EXPORT_NAMES:
        export_line = f'    "{name}",'

        if export_line in updated[
            all_start:closing_index
        ]:
            continue

        updated = (
            updated[:closing_index]
            + export_line
            + "\n"
            + updated[closing_index:]
        )

        closing_index += len(
            export_line
        ) + 1

    PACKAGE_INIT_PATH.write_text(
        updated,
        encoding="utf-8",
    )

    print(
        f"[OK] Updated {PACKAGE_INIT_PATH}"
    )


def main() -> None:
    print("========================================")
    print(" OLA-020 INSTALLER")
    print(" Oracle Service Isolation and")
    print(" Canonical Intelligence Handoff Contract")
    print("========================================")

    write_file(
        MODULE_PATH,
        MODULE_CONTENT,
    )

    write_file(
        TEST_PATH,
        TEST_CONTENT,
    )

    update_package_exports()

    print()
    print("[DONE] OLA-020 installed")
    print()
    print("Run:")
    print(
        "py test_ola_020_oracle_service_isolation_"
        "canonical_intelligence_handoff_contract.py"
    )


if __name__ == "__main__":
    main()