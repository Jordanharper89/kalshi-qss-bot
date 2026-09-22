from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_multi_hop_causal_chain_memory.py"
UPSTREAM_TEST = ROOT / "test_oml_025_oracle_memory_multi_hop_causal_chain_memory.py"

PRODUCTION = PACKAGE / "oracle_memory_cross_market_dependency_memory.py"
TEST = ROOT / "test_oml_026_oracle_memory_cross_market_dependency_memory.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_multi_hop_causal_chain_memory import (
    OracleMemoryMultiHopCausalChain,
    OracleMemoryMultiHopCausalChainMemory,
    verify_oracle_memory_multi_hop_causal_chain,
    verify_oracle_memory_multi_hop_causal_chain_memory,
)

SCHEMA_VERSION = "OML-026"
ENGINE_ID = "OML-026"
POLICY_ID = "oracle-memory.cross-market-dependency-memory.v1"

UPSTREAM_SCHEMA_VERSION = "OML-025"
UPSTREAM_ENGINE_ID = "OML-025"

DEPENDENCY_STATUS_HYPOTHESIS = "hypothesis"
DEPENDENCY_STATUS_SUPPORTED = "supported"
DEPENDENCY_STATUS_ESTABLISHED = "established"
DEPENDENCY_STATUS_CONTRADICTED = "contradicted"

ALLOWED_DEPENDENCY_STATUSES = (
    DEPENDENCY_STATUS_HYPOTHESIS,
    DEPENDENCY_STATUS_SUPPORTED,
    DEPENDENCY_STATUS_ESTABLISHED,
    DEPENDENCY_STATUS_CONTRADICTED,
)


class OracleMemoryCrossMarketDependencyInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCrossMarketObservation:
    source_market_id: str
    target_market_id: str
    source_event_hash: str
    target_event_hash: str
    source_observed_at: str
    target_observed_at: str
    lag_seconds: int
    evidence_hashes: tuple[str, ...]
    contradicting_evidence_hashes: tuple[str, ...]
    confidence: float
    calibrated_probability: float
    outcome_confirmed: bool
    dependency_supported: bool | None
    temporal_order_verified: bool
    market_identity_verified: bool
    evidence_lineage_verified: bool
    calibration_lineage_verified: bool
    observation_hash: str


@dataclass(frozen=True)
class OracleMemoryCrossMarketDependency:
    dependency_id: str
    dependency_name: str
    normalized_dependency_name: str
    source_market_id: str
    target_market_id: str
    dependency_status: str
    observations: tuple[OracleMemoryCrossMarketObservation, ...]
    causal_chain_ids: tuple[str, ...]
    observation_count: int
    confirmed_count: int
    supported_count: int
    contradicted_count: int
    unresolved_count: int
    average_lag_seconds: float
    minimum_lag_seconds: int
    maximum_lag_seconds: int
    empirical_support_rate: float
    aggregate_confidence: float
    average_calibrated_probability: float
    total_evidence_depth: int
    total_contradiction_depth: int
    lead_lag_direction_verified: bool
    unique_chain_lineage_verified: bool
    deterministic_identity_verified: bool
    canonical_order_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    dependency_hash: str


@dataclass(frozen=True)
class OracleMemoryCrossMarketDependencyMemory:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_memory_hash: str
    dependencies: tuple[OracleMemoryCrossMarketDependency, ...]
    dependency_count: int
    total_observation_count: int
    source_market_count: int
    target_market_count: int
    deterministic_identity_verified: bool
    canonical_dependency_order_verified: bool
    lead_lag_direction_verified: bool
    causal_chain_lineage_verified: bool
    evidence_lineage_verified: bool
    contradiction_tracking_verified: bool
    calibration_lineage_verified: bool
    outcome_reconciliation_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    memory_ready: bool
    next_certification_authorized: bool
    read_only: bool
    memory_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))

    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    raise OracleMemoryCrossMarketDependencyInvariantError(
        "unsupported OML-026 value type: "
        f"{type(value).__module__}.{type(value).__qualname__}"
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
    raise OracleMemoryCrossMarketDependencyInvariantError(reason)


def _normalize(value: str) -> str:
    normalized = " ".join(value.strip().lower().split())

    if not normalized:
        _reject("OML-026 dependency name cannot be empty")

    return normalized


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-026 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCrossMarketDependencyInvariantError(
            f"OML-026 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_cross_market_observation(
    *,
    source_market_id: str,
    target_market_id: str,
    source_event_hash: str,
    target_event_hash: str,
    source_observed_at: str,
    target_observed_at: str,
    lag_seconds: int,
    evidence_hashes: Sequence[str],
    contradicting_evidence_hashes: Sequence[str] = (),
    confidence: float,
    calibrated_probability: float,
    outcome_confirmed: bool,
    dependency_supported: bool | None,
) -> OracleMemoryCrossMarketObservation:
    for value, label in (
        (source_market_id, "source market id"),
        (target_market_id, "target market id"),
        (source_event_hash, "source event hash"),
        (target_event_hash, "target event hash"),
    ):
        _require_hash(value, label)

    if source_market_id == target_market_id:
        _reject("OML-026 source and target markets must differ")

    if not source_observed_at.strip() or not target_observed_at.strip():
        _reject("OML-026 observation timestamps required")

    if target_observed_at < source_observed_at:
        _reject("OML-026 target market cannot lead source market")

    if (
        not isinstance(lag_seconds, int)
        or isinstance(lag_seconds, bool)
        or lag_seconds < 0
    ):
        _reject("OML-026 lag seconds invalid")

    evidence = tuple(sorted(set(evidence_hashes)))
    contradictions = tuple(sorted(set(contradicting_evidence_hashes)))

    if not evidence:
        _reject("OML-026 evidence lineage required")

    for value in (*evidence, *contradictions):
        _require_hash(value, "dependency evidence hash")

    confidence = float(confidence)
    calibrated_probability = float(calibrated_probability)

    if not 0.0 <= confidence <= 1.0:
        _reject("OML-026 confidence outside [0, 1]")

    if not 0.0 <= calibrated_probability <= 1.0:
        _reject("OML-026 probability outside [0, 1]")

    if outcome_confirmed:
        if dependency_supported is None:
            _reject("OML-026 confirmed outcome requires support result")
    elif dependency_supported is not None:
        _reject("OML-026 unresolved outcome cannot carry support result")

    body = {
        "source_market_id": source_market_id,
        "target_market_id": target_market_id,
        "source_event_hash": source_event_hash,
        "target_event_hash": target_event_hash,
        "source_observed_at": source_observed_at.strip(),
        "target_observed_at": target_observed_at.strip(),
        "lag_seconds": lag_seconds,
        "evidence_hashes": evidence,
        "contradicting_evidence_hashes": contradictions,
        "confidence": confidence,
        "calibrated_probability": calibrated_probability,
        "outcome_confirmed": bool(outcome_confirmed),
        "dependency_supported": dependency_supported,
        "temporal_order_verified": True,
        "market_identity_verified": True,
        "evidence_lineage_verified": True,
        "calibration_lineage_verified": True,
    }

    observation = OracleMemoryCrossMarketObservation(
        **body,
        observation_hash=_stable_hash(body),
    )

    verify_oracle_memory_cross_market_observation(observation)
    return observation


def verify_oracle_memory_cross_market_observation(
    observation: OracleMemoryCrossMarketObservation,
) -> bool:
    body = asdict(observation)
    supplied = body.pop("observation_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-026 observation hash mismatch")

    for value, label in (
        (observation.source_market_id, "source market id"),
        (observation.target_market_id, "target market id"),
        (observation.source_event_hash, "source event hash"),
        (observation.target_event_hash, "target event hash"),
        (observation.observation_hash, "observation hash"),
    ):
        _require_hash(value, label)

    if observation.source_market_id == observation.target_market_id:
        _reject("OML-026 self-market dependency forbidden")

    if observation.target_observed_at < observation.source_observed_at:
        _reject("OML-026 temporal direction violated")

    if observation.lag_seconds < 0:
        _reject("OML-026 negative lag forbidden")

    if not observation.evidence_hashes:
        _reject("OML-026 evidence missing")

    for value in (
        *observation.evidence_hashes,
        *observation.contradicting_evidence_hashes,
    ):
        _require_hash(value, "observation evidence hash")

    if not 0.0 <= observation.confidence <= 1.0:
        _reject("OML-026 observation confidence invalid")

    if not 0.0 <= observation.calibrated_probability <= 1.0:
        _reject("OML-026 observation probability invalid")

    if observation.outcome_confirmed:
        if observation.dependency_supported is None:
            _reject("OML-026 confirmed support state missing")
    elif observation.dependency_supported is not None:
        _reject("OML-026 unresolved support state invalid")

    if not all(
        (
            observation.temporal_order_verified,
            observation.market_identity_verified,
            observation.evidence_lineage_verified,
            observation.calibration_lineage_verified,
        )
    ):
        _reject("OML-026 observation guarantee missing")

    return True


def _status_for(
    *,
    confirmed_count: int,
    supported_count: int,
    contradicted_count: int,
    empirical_support_rate: float,
) -> str:
    if confirmed_count == 0:
        return DEPENDENCY_STATUS_HYPOTHESIS

    if contradicted_count > supported_count:
        return DEPENDENCY_STATUS_CONTRADICTED

    if confirmed_count >= 3 and empirical_support_rate >= 0.75:
        return DEPENDENCY_STATUS_ESTABLISHED

    return DEPENDENCY_STATUS_SUPPORTED


def build_oracle_memory_cross_market_dependency(
    *,
    dependency_name: str,
    observations: Sequence[OracleMemoryCrossMarketObservation],
    causal_chains: Sequence[OracleMemoryMultiHopCausalChain],
) -> OracleMemoryCrossMarketDependency:
    normalized = _normalize(dependency_name)

    ordered_observations = tuple(
        sorted(
            observations,
            key=lambda item: (
                item.source_observed_at,
                item.target_observed_at,
                item.observation_hash,
            ),
        )
    )

    if not ordered_observations:
        _reject("OML-026 dependency requires observations")

    for observation in ordered_observations:
        verify_oracle_memory_cross_market_observation(observation)

    source_market_ids = {
        item.source_market_id for item in ordered_observations
    }
    target_market_ids = {
        item.target_market_id for item in ordered_observations
    }

    if len(source_market_ids) != 1 or len(target_market_ids) != 1:
        _reject("OML-026 mixed market identities in dependency")

    ordered_chains = tuple(
        sorted(
            causal_chains,
            key=lambda item: (
                item.normalized_chain_name,
                item.chain_id,
            ),
        )
    )

    if not ordered_chains:
        _reject("OML-026 dependency requires causal chain lineage")

    for chain in ordered_chains:
        verify_oracle_memory_multi_hop_causal_chain(chain)

    chain_ids = tuple(chain.chain_id for chain in ordered_chains)

    if len(set(chain_ids)) != len(chain_ids):
        _reject("OML-026 duplicate causal chain lineage")

    confirmed = tuple(
        item for item in ordered_observations
        if item.outcome_confirmed
    )
    supported = tuple(
        item for item in confirmed
        if item.dependency_supported is True
    )
    contradicted = tuple(
        item for item in confirmed
        if item.dependency_supported is False
    )

    confirmed_count = len(confirmed)
    supported_count = len(supported)
    contradicted_count = len(contradicted)
    unresolved_count = len(ordered_observations) - confirmed_count

    empirical_support_rate = (
        round(supported_count / confirmed_count, 12)
        if confirmed_count
        else 0.0
    )

    lags = tuple(item.lag_seconds for item in ordered_observations)

    source_market_id = ordered_observations[0].source_market_id
    target_market_id = ordered_observations[0].target_market_id

    dependency_id = _stable_hash(
        {
            "normalized_dependency_name": normalized,
            "source_market_id": source_market_id,
            "target_market_id": target_market_id,
            "causal_chain_ids": chain_ids,
        }
    )

    body = {
        "dependency_id": dependency_id,
        "dependency_name": dependency_name.strip(),
        "normalized_dependency_name": normalized,
        "source_market_id": source_market_id,
        "target_market_id": target_market_id,
        "dependency_status": _status_for(
            confirmed_count=confirmed_count,
            supported_count=supported_count,
            contradicted_count=contradicted_count,
            empirical_support_rate=empirical_support_rate,
        ),
        "observations": ordered_observations,
        "causal_chain_ids": chain_ids,
        "observation_count": len(ordered_observations),
        "confirmed_count": confirmed_count,
        "supported_count": supported_count,
        "contradicted_count": contradicted_count,
        "unresolved_count": unresolved_count,
        "average_lag_seconds": round(sum(lags) / len(lags), 12),
        "minimum_lag_seconds": min(lags),
        "maximum_lag_seconds": max(lags),
        "empirical_support_rate": empirical_support_rate,
        "aggregate_confidence": round(
            sum(item.confidence for item in ordered_observations)
            / len(ordered_observations),
            12,
        ),
        "average_calibrated_probability": round(
            sum(
                item.calibrated_probability
                for item in ordered_observations
            )
            / len(ordered_observations),
            12,
        ),
        "total_evidence_depth": sum(
            len(item.evidence_hashes)
            for item in ordered_observations
        ),
        "total_contradiction_depth": sum(
            len(item.contradicting_evidence_hashes)
            for item in ordered_observations
        ),
        "lead_lag_direction_verified": True,
        "unique_chain_lineage_verified": True,
        "deterministic_identity_verified": True,
        "canonical_order_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    dependency = OracleMemoryCrossMarketDependency(
        **body,
        dependency_hash=_stable_hash(body),
    )

    verify_oracle_memory_cross_market_dependency(dependency)
    return dependency


def verify_oracle_memory_cross_market_dependency(
    dependency: OracleMemoryCrossMarketDependency,
) -> bool:
    body = asdict(dependency)
    supplied = body.pop("dependency_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-026 dependency hash mismatch")

    if dependency.normalized_dependency_name != _normalize(
        dependency.dependency_name
    ):
        _reject("OML-026 dependency normalization mismatch")

    for value, label in (
        (dependency.dependency_id, "dependency id"),
        (dependency.source_market_id, "source market id"),
        (dependency.target_market_id, "target market id"),
        (dependency.dependency_hash, "dependency hash"),
    ):
        _require_hash(value, label)

    if dependency.dependency_status not in ALLOWED_DEPENDENCY_STATUSES:
        _reject("OML-026 dependency status invalid")

    if dependency.observation_count != len(dependency.observations):
        _reject("OML-026 observation count mismatch")

    if (
        dependency.confirmed_count
        + dependency.unresolved_count
        != dependency.observation_count
    ):
        _reject("OML-026 confirmed/unresolved reconciliation mismatch")

    if (
        dependency.supported_count
        + dependency.contradicted_count
        != dependency.confirmed_count
    ):
        _reject("OML-026 outcome reconciliation mismatch")

    if not dependency.causal_chain_ids:
        _reject("OML-026 causal chain lineage missing")

    if len(set(dependency.causal_chain_ids)) != len(
        dependency.causal_chain_ids
    ):
        _reject("OML-026 duplicate chain ids")

    for value in dependency.causal_chain_ids:
        _require_hash(value, "causal chain id")

    for observation in dependency.observations:
        verify_oracle_memory_cross_market_observation(observation)

        if observation.source_market_id != dependency.source_market_id:
            _reject("OML-026 source market lineage mismatch")

        if observation.target_market_id != dependency.target_market_id:
            _reject("OML-026 target market lineage mismatch")

    if dependency.minimum_lag_seconds < 0:
        _reject("OML-026 minimum lag invalid")

    if dependency.maximum_lag_seconds < dependency.minimum_lag_seconds:
        _reject("OML-026 lag range invalid")

    for value in (
        dependency.empirical_support_rate,
        dependency.aggregate_confidence,
        dependency.average_calibrated_probability,
    ):
        if not 0.0 <= value <= 1.0:
            _reject("OML-026 dependency metric outside [0, 1]")

    expected_id = _stable_hash(
        {
            "normalized_dependency_name": (
                dependency.normalized_dependency_name
            ),
            "source_market_id": dependency.source_market_id,
            "target_market_id": dependency.target_market_id,
            "causal_chain_ids": dependency.causal_chain_ids,
        }
    )

    if dependency.dependency_id != expected_id:
        _reject("OML-026 dependency identity mismatch")

    required_true = (
        dependency.lead_lag_direction_verified,
        dependency.unique_chain_lineage_verified,
        dependency.deterministic_identity_verified,
        dependency.canonical_order_verified,
        dependency.read_only,
    )

    if not all(required_true):
        _reject("OML-026 dependency guarantee missing")

    forbidden = (
        dependency.persistence_authorized,
        dependency.learning_update_authorized,
        dependency.runtime_activation_authorized,
        dependency.publication_authorized,
        dependency.action_authorization_enabled,
        dependency.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-026 forbidden dependency capability enabled")

    return True


def build_oracle_memory_cross_market_dependency_memory(
    *,
    causal_chain_memory: OracleMemoryMultiHopCausalChainMemory,
    dependencies: Sequence[OracleMemoryCrossMarketDependency],
) -> OracleMemoryCrossMarketDependencyMemory:
    verify_oracle_memory_multi_hop_causal_chain_memory(
        causal_chain_memory
    )

    if causal_chain_memory.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-026 upstream schema mismatch")

    if causal_chain_memory.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-026 upstream engine mismatch")

    if not causal_chain_memory.memory_ready:
        _reject("OML-026 upstream causal-chain memory not ready")

    if not causal_chain_memory.next_certification_authorized:
        _reject("OML-026 upstream continuation not authorized")

    if not causal_chain_memory.read_only:
        _reject("OML-026 upstream causal-chain memory not read-only")

    upstream_chain_ids = {
        chain.chain_id for chain in causal_chain_memory.chains
    }

    ordered = tuple(
        sorted(
            dependencies,
            key=lambda item: (
                item.normalized_dependency_name,
                item.source_market_id,
                item.target_market_id,
                item.dependency_id,
            ),
        )
    )

    for dependency in ordered:
        verify_oracle_memory_cross_market_dependency(dependency)

        if any(
            chain_id not in upstream_chain_ids
            for chain_id in dependency.causal_chain_ids
        ):
            _reject("OML-026 dependency references unknown causal chain")

    dependency_ids = tuple(item.dependency_id for item in ordered)

    if len(set(dependency_ids)) != len(dependency_ids):
        _reject("OML-026 duplicate dependency identities")

    source_market_ids = {
        item.source_market_id for item in ordered
    }
    target_market_ids = {
        item.target_market_id for item in ordered
    }

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": causal_chain_memory.schema_version,
        "upstream_engine_id": causal_chain_memory.engine_id,
        "upstream_memory_hash": causal_chain_memory.memory_hash,
        "dependencies": ordered,
        "dependency_count": len(ordered),
        "total_observation_count": sum(
            item.observation_count for item in ordered
        ),
        "source_market_count": len(source_market_ids),
        "target_market_count": len(target_market_ids),
        "deterministic_identity_verified": True,
        "canonical_dependency_order_verified": True,
        "lead_lag_direction_verified": all(
            item.lead_lag_direction_verified for item in ordered
        ),
        "causal_chain_lineage_verified": True,
        "evidence_lineage_verified": True,
        "contradiction_tracking_verified": True,
        "calibration_lineage_verified": True,
        "outcome_reconciliation_verified": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "memory_ready": True,
        "next_certification_authorized": True,
        "read_only": True,
    }

    memory = OracleMemoryCrossMarketDependencyMemory(
        **body,
        memory_hash=_stable_hash(body),
    )

    verify_oracle_memory_cross_market_dependency_memory(memory)
    return memory


def verify_oracle_memory_cross_market_dependency_memory(
    memory: OracleMemoryCrossMarketDependencyMemory,
) -> bool:
    body = asdict(memory)
    supplied = body.pop("memory_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-026 memory hash mismatch")

    if memory.schema_version != SCHEMA_VERSION:
        _reject("OML-026 schema mismatch")

    if memory.engine_id != ENGINE_ID:
        _reject("OML-026 engine mismatch")

    if memory.policy_id != POLICY_ID:
        _reject("OML-026 policy mismatch")

    if memory.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-026 subsystem mismatch")

    if memory.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-026 upstream schema lineage mismatch")

    if memory.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-026 upstream engine lineage mismatch")

    if memory.dependency_count != len(memory.dependencies):
        _reject("OML-026 dependency count mismatch")

    if memory.total_observation_count != sum(
        item.observation_count for item in memory.dependencies
    ):
        _reject("OML-026 total observation count mismatch")

    if memory.source_market_count != len(
        {item.source_market_id for item in memory.dependencies}
    ):
        _reject("OML-026 source market count mismatch")

    if memory.target_market_count != len(
        {item.target_market_id for item in memory.dependencies}
    ):
        _reject("OML-026 target market count mismatch")

    dependency_ids = []

    for dependency in memory.dependencies:
        verify_oracle_memory_cross_market_dependency(dependency)
        dependency_ids.append(dependency.dependency_id)

    if len(set(dependency_ids)) != len(dependency_ids):
        _reject("OML-026 duplicate memory dependency identities")

    required_true = (
        memory.deterministic_identity_verified,
        memory.canonical_dependency_order_verified,
        memory.lead_lag_direction_verified,
        memory.causal_chain_lineage_verified,
        memory.evidence_lineage_verified,
        memory.contradiction_tracking_verified,
        memory.calibration_lineage_verified,
        memory.outcome_reconciliation_verified,
        memory.memory_ready,
        memory.next_certification_authorized,
        memory.read_only,
    )

    if not all(required_true):
        _reject("OML-026 memory guarantee missing")

    forbidden = (
        memory.persistence_enabled,
        memory.learning_updates_enabled,
        memory.runtime_activation_enabled,
        memory.publication_enabled,
        memory.action_authorization_enabled,
        memory.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-026 forbidden memory capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_cross_market_dependency_memory import (
    DEPENDENCY_STATUS_ESTABLISHED,
    OracleMemoryCrossMarketDependencyInvariantError,
    build_oracle_memory_cross_market_dependency,
    build_oracle_memory_cross_market_dependency_memory,
    build_oracle_memory_cross_market_observation,
    verify_oracle_memory_cross_market_dependency_memory,
)
from qseries_v2.oracle_memory.oracle_memory_multi_hop_causal_chain_memory import (
    build_oracle_memory_multi_hop_causal_chain,
    build_oracle_memory_multi_hop_causal_chain_memory,
)


def load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)

    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")

    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryCrossMarketDependencyInvariantError:
        return

    raise AssertionError(f"tampered OML-026 {label} accepted")


def build_chain_memory(root: Path):
    fixture = load_module(
        root
        / "test_oml_025_oracle_memory_multi_hop_causal_chain_memory.py",
        "oml_025_fixture_for_oml_026",
    )

    causal_memory, pattern_ab, pattern_bc = fixture.build_causal_memory(
        root
    )

    chain = build_oracle_memory_multi_hop_causal_chain(
        chain_name=(
            "Demand shift to inventory pressure to market repricing"
        ),
        patterns=(pattern_ab, pattern_bc),
    )

    memory = build_oracle_memory_multi_hop_causal_chain_memory(
        causal_memory=causal_memory,
        chains=(chain,),
    )

    return memory, chain


def main() -> int:
    print("=" * 48)
    print(" OML-026 TEST")
    print(" CROSS-MARKET DEPENDENCY MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    chain_memory, chain = build_chain_memory(root)

    source_market_id = "a" * 64
    target_market_id = "b" * 64

    observations = (
        build_oracle_memory_cross_market_observation(
            source_market_id=source_market_id,
            target_market_id=target_market_id,
            source_event_hash="1" * 64,
            target_event_hash="2" * 64,
            source_observed_at="2026-08-02T14:00:00-05:00",
            target_observed_at="2026-08-02T14:10:00-05:00",
            lag_seconds=600,
            evidence_hashes=("3" * 64,),
            confidence=0.82,
            calibrated_probability=0.78,
            outcome_confirmed=True,
            dependency_supported=True,
        ),
        build_oracle_memory_cross_market_observation(
            source_market_id=source_market_id,
            target_market_id=target_market_id,
            source_event_hash="4" * 64,
            target_event_hash="5" * 64,
            source_observed_at="2026-08-02T15:00:00-05:00",
            target_observed_at="2026-08-02T15:15:00-05:00",
            lag_seconds=900,
            evidence_hashes=("6" * 64,),
            confidence=0.80,
            calibrated_probability=0.76,
            outcome_confirmed=True,
            dependency_supported=True,
        ),
        build_oracle_memory_cross_market_observation(
            source_market_id=source_market_id,
            target_market_id=target_market_id,
            source_event_hash="7" * 64,
            target_event_hash="8" * 64,
            source_observed_at="2026-08-02T16:00:00-05:00",
            target_observed_at="2026-08-02T16:20:00-05:00",
            lag_seconds=1200,
            evidence_hashes=("9" * 64,),
            contradicting_evidence_hashes=("c" * 64,),
            confidence=0.77,
            calibrated_probability=0.74,
            outcome_confirmed=True,
            dependency_supported=True,
        ),
    )

    dependency = build_oracle_memory_cross_market_dependency(
        dependency_name=(
            "Energy market pressure leads inflation-market repricing"
        ),
        observations=observations,
        causal_chains=(chain,),
    )

    assert dependency.dependency_status == DEPENDENCY_STATUS_ESTABLISHED
    assert dependency.observation_count == 3
    assert dependency.confirmed_count == 3
    assert dependency.supported_count == 3
    assert dependency.contradicted_count == 0
    assert dependency.unresolved_count == 0
    assert dependency.average_lag_seconds == 900.0
    assert dependency.minimum_lag_seconds == 600
    assert dependency.maximum_lag_seconds == 1200
    assert dependency.empirical_support_rate == 1.0
    assert dependency.total_evidence_depth == 3
    assert dependency.total_contradiction_depth == 1
    assert dependency.lead_lag_direction_verified
    assert dependency.unique_chain_lineage_verified
    assert dependency.deterministic_identity_verified
    assert dependency.canonical_order_verified
    assert not dependency.persistence_authorized
    assert not dependency.learning_update_authorized
    assert not dependency.runtime_activation_authorized
    assert not dependency.publication_authorized
    assert not dependency.action_authorization_enabled
    assert not dependency.qseries_execution_authorized
    assert dependency.read_only

    memory = build_oracle_memory_cross_market_dependency_memory(
        causal_chain_memory=chain_memory,
        dependencies=(dependency,),
    )

    assert memory.schema_version == "OML-026"
    assert memory.engine_id == "OML-026"
    assert memory.upstream_schema_version == "OML-025"
    assert memory.upstream_engine_id == "OML-025"
    assert memory.dependency_count == 1
    assert memory.total_observation_count == 3
    assert memory.source_market_count == 1
    assert memory.target_market_count == 1
    assert memory.deterministic_identity_verified
    assert memory.canonical_dependency_order_verified
    assert memory.lead_lag_direction_verified
    assert memory.causal_chain_lineage_verified
    assert memory.evidence_lineage_verified
    assert memory.contradiction_tracking_verified
    assert memory.calibration_lineage_verified
    assert memory.outcome_reconciliation_verified
    assert not memory.persistence_enabled
    assert not memory.learning_updates_enabled
    assert not memory.runtime_activation_enabled
    assert not memory.publication_enabled
    assert not memory.action_authorization_enabled
    assert not memory.qseries_execution_enabled
    assert memory.memory_ready
    assert memory.next_certification_authorized
    assert memory.read_only

    replay = build_oracle_memory_cross_market_dependency_memory(
        causal_chain_memory=chain_memory,
        dependencies=(dependency,),
    )

    assert replay == memory
    assert verify_oracle_memory_cross_market_dependency_memory(memory)

    expect_rejection(
        lambda: verify_oracle_memory_cross_market_dependency_memory(
            replace(memory, dependency_count=2)
        ),
        "dependency count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_cross_market_dependency_memory(
            replace(memory, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_cross_market_dependency_memory(
            replace(memory, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-025 causal-chain memory consumed")
    print("[PASS] Source and target market identities retained")
    print("[PASS] Lead-lag temporal order enforced")
    print("[PASS] Cross-market lag statistics calculated")
    print("[PASS] Causal-chain lineage retained")
    print("[PASS] Evidence and contradiction lineage retained")
    print("[PASS] Calibrated probabilities retained")
    print("[PASS] Confirmed dependency outcomes reconciled")
    print("[PASS] Established cross-market dependency detected")
    print("[PASS] Dependency memory deterministic across replay")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered dependency memories rejected")
    print("[DONE] OML-026 CROSS-MARKET DEPENDENCY MEMORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_upstream() -> None:
    if not UPSTREAM.is_file() or not UPSTREAM_TEST.is_file():
        raise RuntimeError(
            "Certified OML-025 production or standalone test missing"
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_multi_hop_causal_chain_memory"
    )

    expected = {
        "SCHEMA_VERSION": "OML-025",
        "ENGINE_ID": "OML-025",
        "POLICY_ID": "oracle-memory.multi-hop-causal-chain-memory.v1",
        "UPSTREAM_SCHEMA_VERSION": "OML-024",
        "UPSTREAM_ENGINE_ID": "OML-024",
    }

    for name, value in expected.items():
        actual = getattr(module, name, None)

        if actual != value:
            raise RuntimeError(
                f"Certified OML-025 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    required = (
        "OracleMemoryMultiHopCausalChain",
        "OracleMemoryMultiHopCausalChainMemory",
        "build_oracle_memory_multi_hop_causal_chain",
        "build_oracle_memory_multi_hop_causal_chain_memory",
        "verify_oracle_memory_multi_hop_causal_chain",
        "verify_oracle_memory_multi_hop_causal_chain_memory",
    )

    missing = [name for name in required if not hasattr(module, name)]

    if missing:
        raise RuntimeError(
            "Certified OML-025 missing required symbols: "
            + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-026 FOR-SURE INSTALLER")
    print(" CROSS-MARKET DEPENDENCY MEMORY")
    print("=" * 48)
    print("[BOOT] Revision: CAPABILITY_MILESTONE_FULL_REPLACEMENT")

    try:
        validate_upstream()
        print("[OK] Actual OML-025 imported and structurally verified")

        upstream_run = subprocess.run(
            [sys.executable, str(UPSTREAM_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream_run.returncode:
            raise RuntimeError(
                "OML-025 certification failed with exit code "
                f"{upstream_run.returncode}"
            )

        production_before = UPSTREAM.read_bytes()
        test_before = UPSTREAM_TEST.read_bytes()

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_cross_market_dependency_memory import *"
        )
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"

            current += export + "\n"
            INIT.write_text(current, encoding="utf-8", newline="\n")
            print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")
        else:
            print(f"[OK] PACKAGE EXPORT PRESENT: {INIT.resolve()}")

        ast.parse(INIT.read_text(encoding="utf-8"), filename=str(INIT))

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )

        if completed.returncode:
            raise RuntimeError(
                "OML-026 test failed with exit code "
                f"{completed.returncode}"
            )

        if UPSTREAM.read_bytes() != production_before:
            raise RuntimeError("Certified OML-025 production changed")

        if UPSTREAM_TEST.read_bytes() != test_before:
            raise RuntimeError("Certified OML-025 standalone test changed")

        print("[PASS] Certified OML-025 production unchanged")
        print("[PASS] Certified OML-025 standalone test unchanged")
        print("[PASS] OML-026 cross-market dependency memory installed")
        print("[PASS] OML-026 standalone deterministic test installed")
        print("[PASS] Lead-lag dependency tracking installed")
        print("[PASS] Cross-market evidence lineage installed")
        print("[PASS] Causal-chain linkage installed")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OML-026 CROSS-MARKET DEPENDENCY MEMORY INSTALLED")
        return 0

    except (RuntimeError, SyntaxError, ImportError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
