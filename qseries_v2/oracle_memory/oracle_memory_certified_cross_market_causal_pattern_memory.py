from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_calibration_memory import (
    OracleMemoryCertifiedCrossMarketCalibrationMemory,
    verify_oracle_memory_certified_cross_market_calibration_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_causal_pattern_memory import (
    OracleMemoryCertifiedCausalObservationRequest,
    OracleMemoryCertifiedCausalPatternMemory,
    build_oracle_memory_certified_causal_pattern_memory,
    verify_oracle_memory_certified_causal_observation_request,
    verify_oracle_memory_certified_causal_pattern_memory,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-049"
ENGINE_ID = "OML-049"
POLICY_ID = "oracle-memory.certified-cross-market-causal-pattern-memory.v1"
UPSTREAM_SCHEMA_VERSION = "OML-048"
UPSTREAM_ENGINE_ID = "OML-048"
CAUSAL_SCHEMA_VERSION = "OML-036"
CAUSAL_ENGINE_ID = "OML-036"
STATE_READ_ONLY = "read_only_cross_market_causal_pattern_memory"


class OracleMemoryCertifiedCrossMarketCausalInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedCrossMarketCausalPatternMemory:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_calibration_certification_hash: str
    upstream_calibration_memory_hash: str
    causal_schema_version: str
    causal_engine_id: str
    causal_patterns: OracleMemoryCertifiedCausalPatternMemory
    pattern_count: int
    total_observation_count: int
    state: str
    calibration_lineage_verified: bool
    certified_observation_lineage_verified: bool
    deterministic_identity_verified: bool
    canonical_pattern_order_verified: bool
    temporal_precedence_verified: bool
    evidence_lineage_verified: bool
    contradiction_tracking_verified: bool
    outcome_reconciliation_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    causal_memory_ready: bool
    downstream_multi_hop_causal_authorized: bool
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
    raise OracleMemoryCertifiedCrossMarketCausalInvariantError(
        "unsupported OML-049 value type"
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
    raise OracleMemoryCertifiedCrossMarketCausalInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-049 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedCrossMarketCausalInvariantError(
            f"OML-049 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_cross_market_causal_pattern_memory(
    *,
    calibration: OracleMemoryCertifiedCrossMarketCalibrationMemory,
    requests: Sequence[OracleMemoryCertifiedCausalObservationRequest],
) -> OracleMemoryCertifiedCrossMarketCausalPatternMemory:
    verify_oracle_memory_certified_cross_market_calibration_memory(calibration)

    if calibration.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-049 upstream schema mismatch")
    if calibration.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-049 upstream engine mismatch")
    if not calibration.calibration_ready:
        _reject("OML-049 upstream calibration not ready")
    if not calibration.downstream_causal_memory_authorized:
        _reject("OML-049 causal continuation not authorized")
    if not calibration.read_only:
        _reject("OML-049 upstream calibration not read-only")

    allowed_hashes = {
        value
        for binding in calibration.calibration.bindings
        for value in binding.certified_observation_hashes
    }
    if not allowed_hashes:
        _reject("OML-049 no certified observation hashes available")

    for request in requests:
        verify_oracle_memory_certified_causal_observation_request(request)
        referenced = set(request.certified_observation_hashes)
        contradicted = set(request.contradicting_certified_observation_hashes)
        if not referenced.issubset(allowed_hashes):
            _reject("OML-049 unknown certified causal evidence")
        if not contradicted.issubset(allowed_hashes):
            _reject("OML-049 unknown certified contradiction evidence")

    causal_patterns = build_oracle_memory_certified_causal_pattern_memory(
        calibration=calibration.calibration,
        requests=tuple(requests),
    )
    verify_oracle_memory_certified_causal_pattern_memory(causal_patterns)

    if causal_patterns.schema_version != CAUSAL_SCHEMA_VERSION:
        _reject("OML-049 causal schema mismatch")
    if causal_patterns.engine_id != CAUSAL_ENGINE_ID:
        _reject("OML-049 causal engine mismatch")
    if causal_patterns.upstream_certification_hash != (
        calibration.calibration.certification_hash
    ):
        _reject("OML-049 calibration certification lineage mismatch")
    if causal_patterns.upstream_calibration_memory_hash != (
        calibration.calibration.calibration_memory.memory_hash
    ):
        _reject("OML-049 calibration memory lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": calibration.schema_version,
        "upstream_engine_id": calibration.engine_id,
        "upstream_certification_hash": calibration.certification_hash,
        "upstream_calibration_certification_hash": (
            calibration.calibration.certification_hash
        ),
        "upstream_calibration_memory_hash": (
            calibration.calibration.calibration_memory.memory_hash
        ),
        "causal_schema_version": causal_patterns.schema_version,
        "causal_engine_id": causal_patterns.engine_id,
        "causal_patterns": causal_patterns,
        "pattern_count": causal_patterns.pattern_count,
        "total_observation_count": causal_patterns.total_observation_count,
        "state": STATE_READ_ONLY,
        "calibration_lineage_verified": True,
        "certified_observation_lineage_verified": (
            causal_patterns.certified_observation_lineage_verified
        ),
        "deterministic_identity_verified": (
            causal_patterns.deterministic_identity_verified
        ),
        "canonical_pattern_order_verified": (
            causal_patterns.canonical_pattern_order_verified
        ),
        "temporal_precedence_verified": (
            causal_patterns.temporal_precedence_verified
        ),
        "evidence_lineage_verified": causal_patterns.evidence_lineage_verified,
        "contradiction_tracking_verified": (
            causal_patterns.contradiction_tracking_verified
        ),
        "outcome_reconciliation_verified": (
            causal_patterns.outcome_reconciliation_verified
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "causal_memory_ready": True,
        "downstream_multi_hop_causal_authorized": (
            causal_patterns.downstream_multi_hop_causal_authorized
        ),
        "read_only": True,
    }

    result = OracleMemoryCertifiedCrossMarketCausalPatternMemory(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_cross_market_causal_pattern_memory(result)
    return result


def verify_oracle_memory_certified_cross_market_causal_pattern_memory(
    result: OracleMemoryCertifiedCrossMarketCausalPatternMemory,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-049 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-049 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-049 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-049 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-049 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-049 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-049 upstream engine lineage mismatch")
    if result.causal_schema_version != CAUSAL_SCHEMA_VERSION:
        _reject("OML-049 causal schema lineage mismatch")
    if result.causal_engine_id != CAUSAL_ENGINE_ID:
        _reject("OML-049 causal engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_calibration_certification_hash,
        result.upstream_calibration_memory_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_oracle_memory_certified_causal_pattern_memory(
        result.causal_patterns
    )

    if result.upstream_calibration_certification_hash != (
        result.causal_patterns.upstream_certification_hash
    ):
        _reject("OML-049 calibration certification mismatch")
    if result.upstream_calibration_memory_hash != (
        result.causal_patterns.upstream_calibration_memory_hash
    ):
        _reject("OML-049 calibration memory mismatch")
    if result.pattern_count != result.causal_patterns.pattern_count:
        _reject("OML-049 pattern count mismatch")
    if result.total_observation_count != (
        result.causal_patterns.total_observation_count
    ):
        _reject("OML-049 observation count mismatch")

    required = (
        result.calibration_lineage_verified,
        result.certified_observation_lineage_verified,
        result.deterministic_identity_verified,
        result.canonical_pattern_order_verified,
        result.temporal_precedence_verified,
        result.evidence_lineage_verified,
        result.contradiction_tracking_verified,
        result.outcome_reconciliation_verified,
        result.causal_memory_ready,
        result.downstream_multi_hop_causal_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-049 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-049 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-049 forbidden capability enabled")

    return True
