from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_source_reliability import (
    OracleMemoryCertifiedCrossMarketSourceReliability,
    verify_oracle_memory_certified_cross_market_source_reliability,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_calibration_memory import (
    OracleMemoryCertifiedCalibrationForecast,
    OracleMemoryCertifiedCalibrationMemory,
    build_oracle_memory_certified_calibration_memory,
    verify_oracle_memory_certified_calibration_forecast,
    verify_oracle_memory_certified_calibration_memory,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-048"
ENGINE_ID = "OML-048"
POLICY_ID = "oracle-memory.certified-cross-market-calibration-memory.v1"
UPSTREAM_SCHEMA_VERSION = "OML-047"
UPSTREAM_ENGINE_ID = "OML-047"
CALIBRATION_SCHEMA_VERSION = "OML-035"
CALIBRATION_ENGINE_ID = "OML-035"
STATE_READ_ONLY = "read_only_cross_market_calibration_memory"


class OracleMemoryCertifiedCrossMarketCalibrationInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedCrossMarketCalibrationMemory:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_reliability_certification_hash: str
    upstream_reliability_memory_hash: str
    calibration_schema_version: str
    calibration_engine_id: str
    calibration: OracleMemoryCertifiedCalibrationMemory
    profile_count: int
    total_observation_count: int
    total_confirmed_count: int
    state: str
    source_reliability_lineage_verified: bool
    certified_observation_lineage_verified: bool
    calibration_lineage_verified: bool
    deterministic_scoring_verified: bool
    canonical_profile_order_verified: bool
    probability_bounds_verified: bool
    outcome_lineage_verified: bool
    calibration_bucket_reconciliation_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    calibration_ready: bool
    downstream_causal_memory_authorized: bool
    read_only: bool
    certification_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleMemoryCertifiedCrossMarketCalibrationInvariantError(
        "unsupported OML-048 value type"
    )


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _canonical(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _reject(reason: str) -> None:
    raise OracleMemoryCertifiedCrossMarketCalibrationInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-048 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedCrossMarketCalibrationInvariantError(
            f"OML-048 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_cross_market_calibration_memory(
    *,
    reliability: OracleMemoryCertifiedCrossMarketSourceReliability,
    forecasts: Sequence[OracleMemoryCertifiedCalibrationForecast],
) -> OracleMemoryCertifiedCrossMarketCalibrationMemory:
    verify_oracle_memory_certified_cross_market_source_reliability(reliability)

    if reliability.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-048 upstream schema mismatch")
    if reliability.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-048 upstream engine mismatch")
    if not reliability.reliability_ready:
        _reject("OML-048 upstream reliability not ready")
    if not reliability.downstream_calibration_authorized:
        _reject("OML-048 calibration continuation not authorized")
    if not reliability.read_only:
        _reject("OML-048 upstream reliability not read-only")

    allowed_hashes = {
        value
        for binding in reliability.source_reliability.bindings
        for value in binding.certified_observation_hashes
    }
    if not allowed_hashes:
        _reject("OML-048 no certified observation hashes available")

    for forecast in forecasts:
        verify_oracle_memory_certified_calibration_forecast(forecast)
        if forecast.certified_observation_hash not in allowed_hashes:
            _reject("OML-048 forecast references unknown certified observation")

    calibration = build_oracle_memory_certified_calibration_memory(
        source_reliability=reliability.source_reliability,
        forecasts=tuple(forecasts),
    )
    verify_oracle_memory_certified_calibration_memory(calibration)

    if calibration.schema_version != CALIBRATION_SCHEMA_VERSION:
        _reject("OML-048 calibration schema mismatch")
    if calibration.engine_id != CALIBRATION_ENGINE_ID:
        _reject("OML-048 calibration engine mismatch")
    if calibration.upstream_certification_hash != (
        reliability.source_reliability.certification_hash
    ):
        _reject("OML-048 reliability certification lineage mismatch")
    if calibration.upstream_reliability_memory_hash != (
        reliability.source_reliability.reliability_memory.memory_hash
    ):
        _reject("OML-048 reliability memory lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": reliability.schema_version,
        "upstream_engine_id": reliability.engine_id,
        "upstream_certification_hash": reliability.certification_hash,
        "upstream_reliability_certification_hash": (
            reliability.source_reliability.certification_hash
        ),
        "upstream_reliability_memory_hash": (
            reliability.source_reliability.reliability_memory.memory_hash
        ),
        "calibration_schema_version": calibration.schema_version,
        "calibration_engine_id": calibration.engine_id,
        "calibration": calibration,
        "profile_count": calibration.profile_count,
        "total_observation_count": calibration.total_observation_count,
        "total_confirmed_count": calibration.total_confirmed_count,
        "state": STATE_READ_ONLY,
        "source_reliability_lineage_verified": True,
        "certified_observation_lineage_verified": (
            calibration.certified_observation_lineage_verified
        ),
        "calibration_lineage_verified": True,
        "deterministic_scoring_verified": (
            calibration.deterministic_scoring_verified
        ),
        "canonical_profile_order_verified": (
            calibration.canonical_profile_order_verified
        ),
        "probability_bounds_verified": calibration.probability_bounds_verified,
        "outcome_lineage_verified": calibration.outcome_lineage_verified,
        "calibration_bucket_reconciliation_verified": (
            calibration.calibration_bucket_reconciliation_verified
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "calibration_ready": True,
        "downstream_causal_memory_authorized": (
            calibration.downstream_causal_memory_authorized
        ),
        "read_only": True,
    }

    result = OracleMemoryCertifiedCrossMarketCalibrationMemory(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_cross_market_calibration_memory(result)
    return result


def verify_oracle_memory_certified_cross_market_calibration_memory(
    result: OracleMemoryCertifiedCrossMarketCalibrationMemory,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-048 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-048 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-048 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-048 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-048 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-048 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-048 upstream engine lineage mismatch")
    if result.calibration_schema_version != CALIBRATION_SCHEMA_VERSION:
        _reject("OML-048 calibration schema lineage mismatch")
    if result.calibration_engine_id != CALIBRATION_ENGINE_ID:
        _reject("OML-048 calibration engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_reliability_certification_hash,
        result.upstream_reliability_memory_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_oracle_memory_certified_calibration_memory(result.calibration)

    if result.upstream_reliability_certification_hash != (
        result.calibration.upstream_certification_hash
    ):
        _reject("OML-048 reliability certification mismatch")
    if result.upstream_reliability_memory_hash != (
        result.calibration.upstream_reliability_memory_hash
    ):
        _reject("OML-048 reliability memory mismatch")
    if result.profile_count != result.calibration.profile_count:
        _reject("OML-048 profile count mismatch")
    if result.total_observation_count != (
        result.calibration.total_observation_count
    ):
        _reject("OML-048 observation count mismatch")
    if result.total_confirmed_count != (
        result.calibration.total_confirmed_count
    ):
        _reject("OML-048 confirmed count mismatch")

    required = (
        result.source_reliability_lineage_verified,
        result.certified_observation_lineage_verified,
        result.calibration_lineage_verified,
        result.deterministic_scoring_verified,
        result.canonical_profile_order_verified,
        result.probability_bounds_verified,
        result.outcome_lineage_verified,
        result.calibration_bucket_reconciliation_verified,
        result.calibration_ready,
        result.downstream_causal_memory_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-048 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-048 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-048 forbidden capability enabled")

    return True
