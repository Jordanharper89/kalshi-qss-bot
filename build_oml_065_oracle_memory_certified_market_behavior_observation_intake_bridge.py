from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_certified_market_behavior_cross_market_dependency_memory.py"
UPSTREAM_TEST = ROOT / "test_oml_064_oracle_memory_certified_market_behavior_cross_market_dependency_memory.py"
INTAKE_MODULE = PACKAGE / "oracle_memory_certified_observation_intake_contract.py"
INTAKE_TEST = ROOT / "test_oml_027_oracle_memory_certified_observation_intake_contract.py"

PRODUCTION = PACKAGE / "oracle_memory_certified_market_behavior_observation_intake_bridge.py"
TEST = ROOT / "test_oml_065_oracle_memory_certified_market_behavior_observation_intake_bridge.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_cross_market_dependency_memory import (
    OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory,
    verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_intake_contract import (
    OBSERVATION_KIND_MARKET,
    OracleMemoryCertifiedObservation,
    OracleMemoryObservationIntakeBatch,
    build_oracle_memory_certified_observation,
    build_oracle_memory_observation_intake_batch,
    verify_oracle_memory_certified_observation,
    verify_oracle_memory_observation_intake_batch,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-065"
ENGINE_ID = "OML-065"
POLICY_ID = "oracle-memory.certified-market-behavior-observation-intake-bridge.v1"
UPSTREAM_SCHEMA_VERSION = "OML-064"
UPSTREAM_ENGINE_ID = "OML-064"
INTAKE_SCHEMA_VERSION = "OML-027"
INTAKE_ENGINE_ID = "OML-027"
STATE_READ_ONLY = "read_only_market_behavior_observation_intake_bridge"


class OracleMemoryCertifiedMarketBehaviorObservationIntakeInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedMarketBehaviorObservationIntakeRequest:
    dependency_id: str
    domain_id: str
    entity_key: str
    source_key: str
    observed_at: str
    effective_at: str
    payload: Mapping[str, Any]
    confidence: float
    uncertainty: float
    request_hash: str


@dataclass(frozen=True)
class OracleMemoryCertifiedMarketBehaviorObservationIntakeBinding:
    dependency_id: str
    dependency_hash: str
    observation_id: str
    observation_hash: str
    chain_ids: tuple[str, ...]
    certified_observation_hashes: tuple[str, ...]
    causal_observation_hashes: tuple[str, ...]
    cross_market_observation_hashes: tuple[str, ...]
    upstream_certification_hash: str
    upstream_dependency_memory_hash: str
    intake_batch_hash: str
    dependency_lineage_verified: bool
    chain_lineage_verified: bool
    observation_lineage_verified: bool
    source_certification_verified: bool
    deterministic_binding_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    binding_hash: str


@dataclass(frozen=True)
class OracleMemoryCertifiedMarketBehaviorObservationIntakeBridge:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_dependency_memory_hash: str
    intake_schema_version: str
    intake_engine_id: str
    intake_batch: OracleMemoryObservationIntakeBatch
    bindings: tuple[OracleMemoryCertifiedMarketBehaviorObservationIntakeBinding, ...]
    dependency_count: int
    observation_count: int
    unique_observation_count: int
    duplicate_observation_count: int
    state: str
    dependency_lineage_verified: bool
    chain_lineage_verified: bool
    certified_observation_lineage_verified: bool
    deterministic_hashing_verified: bool
    canonical_order_verified: bool
    duplicate_detection_verified: bool
    source_certification_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    bridge_ready: bool
    downstream_candidate_materialization_authorized: bool
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
    raise OracleMemoryCertifiedMarketBehaviorObservationIntakeInvariantError(
        "unsupported OML-065 value type"
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
    raise OracleMemoryCertifiedMarketBehaviorObservationIntakeInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-065 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedMarketBehaviorObservationIntakeInvariantError(
            f"OML-065 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_market_behavior_observation_intake_request(
    *,
    dependency_id: str,
    domain_id: str,
    entity_key: str,
    source_key: str,
    observed_at: str,
    effective_at: str,
    payload: Mapping[str, Any],
    confidence: float,
    uncertainty: float,
) -> OracleMemoryCertifiedMarketBehaviorObservationIntakeRequest:
    _require_hash(dependency_id, "dependency id")
    if domain_id not in MEMORY_DOMAINS:
        _reject("OML-065 unknown memory domain")
    for label, value in (
        ("entity_key", entity_key),
        ("source_key", source_key),
        ("observed_at", observed_at),
        ("effective_at", effective_at),
    ):
        if not isinstance(value, str) or not value.strip():
            _reject(f"OML-065 {label} required")
    if not isinstance(payload, Mapping):
        _reject("OML-065 payload must be a mapping")
    confidence = float(confidence)
    uncertainty = float(uncertainty)
    if not 0.0 <= confidence <= 1.0:
        _reject("OML-065 confidence outside [0, 1]")
    if not 0.0 <= uncertainty <= 1.0:
        _reject("OML-065 uncertainty outside [0, 1]")
    body = {
        "dependency_id": dependency_id,
        "domain_id": domain_id,
        "entity_key": entity_key.strip(),
        "source_key": source_key.strip(),
        "observed_at": observed_at.strip(),
        "effective_at": effective_at.strip(),
        "payload": _canonical(payload),
        "confidence": confidence,
        "uncertainty": uncertainty,
    }
    result = OracleMemoryCertifiedMarketBehaviorObservationIntakeRequest(
        **body,
        request_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_market_behavior_observation_intake_request(result)
    return result


def verify_oracle_memory_certified_market_behavior_observation_intake_request(
    request: OracleMemoryCertifiedMarketBehaviorObservationIntakeRequest,
) -> bool:
    body = asdict(request)
    supplied = body.pop("request_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-065 request hash mismatch")
    _require_hash(request.dependency_id, "dependency id")
    _require_hash(request.request_hash, "request hash")
    if request.domain_id not in MEMORY_DOMAINS:
        _reject("OML-065 request domain invalid")
    return True


def _build_binding(
    *,
    dependency,
    upstream_binding,
    observation: OracleMemoryCertifiedObservation,
    upstream: OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory,
    intake_batch: OracleMemoryObservationIntakeBatch,
) -> OracleMemoryCertifiedMarketBehaviorObservationIntakeBinding:
    body = {
        "dependency_id": dependency.dependency_id,
        "dependency_hash": dependency.dependency_hash,
        "observation_id": observation.observation_id,
        "observation_hash": observation.observation_hash,
        "chain_ids": upstream_binding.chain_ids,
        "certified_observation_hashes": upstream_binding.certified_observation_hashes,
        "causal_observation_hashes": upstream_binding.causal_observation_hashes,
        "cross_market_observation_hashes": upstream_binding.cross_market_observation_hashes,
        "upstream_certification_hash": upstream.certification_hash,
        "upstream_dependency_memory_hash": upstream.dependencies.dependency_memory.memory_hash,
        "intake_batch_hash": intake_batch.batch_hash,
        "dependency_lineage_verified": True,
        "chain_lineage_verified": True,
        "observation_lineage_verified": True,
        "source_certification_verified": True,
        "deterministic_binding_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }
    result = OracleMemoryCertifiedMarketBehaviorObservationIntakeBinding(
        **body,
        binding_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_market_behavior_observation_intake_binding(result)
    return result


def verify_oracle_memory_certified_market_behavior_observation_intake_binding(
    binding: OracleMemoryCertifiedMarketBehaviorObservationIntakeBinding,
) -> bool:
    body = asdict(binding)
    supplied = body.pop("binding_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-065 binding hash mismatch")
    for value in (
        binding.dependency_id,
        binding.dependency_hash,
        binding.observation_id,
        binding.observation_hash,
        binding.upstream_certification_hash,
        binding.upstream_dependency_memory_hash,
        binding.intake_batch_hash,
        binding.binding_hash,
        *binding.chain_ids,
        *binding.certified_observation_hashes,
        *binding.causal_observation_hashes,
        *binding.cross_market_observation_hashes,
    ):
        _require_hash(value, "binding lineage hash")
    if not all((
        binding.dependency_lineage_verified,
        binding.chain_lineage_verified,
        binding.observation_lineage_verified,
        binding.source_certification_verified,
        binding.deterministic_binding_verified,
        binding.read_only,
    )):
        _reject("OML-065 binding guarantee missing")
    if any((
        binding.persistence_authorized,
        binding.learning_update_authorized,
        binding.runtime_activation_authorized,
        binding.publication_authorized,
        binding.action_authorization_enabled,
        binding.qseries_execution_authorized,
    )):
        _reject("OML-065 forbidden binding capability enabled")
    return True


def build_oracle_memory_certified_market_behavior_observation_intake_bridge(
    *,
    dependencies: OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory,
    requests: Sequence[OracleMemoryCertifiedMarketBehaviorObservationIntakeRequest],
) -> OracleMemoryCertifiedMarketBehaviorObservationIntakeBridge:
    verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory(dependencies)
    if dependencies.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-065 upstream schema mismatch")
    if dependencies.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-065 upstream engine mismatch")
    if not dependencies.dependency_memory_ready:
        _reject("OML-065 upstream dependency memory not ready")
    if not dependencies.downstream_market_behavior_authorized:
        _reject("OML-065 downstream continuation not authorized")
    if not dependencies.read_only:
        _reject("OML-065 upstream dependency memory not read-only")

    dependency_by_id = {
        item.dependency_id: item
        for item in dependencies.dependencies.dependency_memory.dependencies
    }
    binding_by_id = {
        item.dependency_id: item for item in dependencies.dependencies.bindings
    }
    if set(dependency_by_id) != set(binding_by_id):
        _reject("OML-065 upstream dependency/binding mismatch")

    observations = []
    lineage_by_observation_hash = {}
    seen_requests = set()

    for request in requests:
        verify_oracle_memory_certified_market_behavior_observation_intake_request(request)
        if request.request_hash in seen_requests:
            _reject("OML-065 duplicate intake request")
        seen_requests.add(request.request_hash)

        dependency = dependency_by_id.get(request.dependency_id)
        upstream_binding = binding_by_id.get(request.dependency_id)
        if dependency is None or upstream_binding is None:
            _reject("OML-065 unknown dependency id")

        evidence = tuple(sorted(set(
            upstream_binding.certified_observation_hashes
            + upstream_binding.cross_market_observation_hashes
        )))
        parents = tuple(sorted(set(
            upstream_binding.causal_observation_hashes
        )))
        payload = {
            **dict(request.payload),
            "dependency_id": dependency.dependency_id,
            "dependency_hash": dependency.dependency_hash,
            "dependency_name": dependency.dependency_name,
            "dependency_status": dependency.dependency_status,
            "source_market_id": dependency.source_market_id,
            "target_market_id": dependency.target_market_id,
            "average_lag_seconds": dependency.average_lag_seconds,
            "empirical_support_rate": dependency.empirical_support_rate,
            "chain_ids": upstream_binding.chain_ids,
        }

        observation = build_oracle_memory_certified_observation(
            observation_kind=OBSERVATION_KIND_MARKET,
            domain_id=request.domain_id,
            entity_key=request.entity_key,
            source_key=request.source_key,
            observed_at=request.observed_at,
            effective_at=request.effective_at,
            payload=payload,
            evidence_hashes=evidence,
            parent_observation_hashes=parents,
            source_certification_hash=dependencies.certification_hash,
            confidence=request.confidence,
            uncertainty=request.uncertainty,
            contradiction_count=dependency.total_contradiction_depth,
        )
        verify_oracle_memory_certified_observation(observation)
        observations.append(observation)
        lineage_by_observation_hash[observation.observation_hash] = (
            dependency,
            upstream_binding,
        )

    if not observations:
        _reject("OML-065 at least one intake request required")

    intake_batch = build_oracle_memory_observation_intake_batch(
        cross_market_memory=dependencies.dependencies.dependency_memory,
        observations=tuple(observations),
    )
    verify_oracle_memory_observation_intake_batch(intake_batch)

    if intake_batch.schema_version != INTAKE_SCHEMA_VERSION:
        _reject("OML-065 intake schema mismatch")
    if intake_batch.engine_id != INTAKE_ENGINE_ID:
        _reject("OML-065 intake engine mismatch")

    bindings = tuple(
        _build_binding(
            dependency=lineage_by_observation_hash[item.observation_hash][0],
            upstream_binding=lineage_by_observation_hash[item.observation_hash][1],
            observation=item,
            upstream=dependencies,
            intake_batch=intake_batch,
        )
        for item in intake_batch.observations
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": dependencies.schema_version,
        "upstream_engine_id": dependencies.engine_id,
        "upstream_certification_hash": dependencies.certification_hash,
        "upstream_dependency_memory_hash": dependencies.dependencies.dependency_memory.memory_hash,
        "intake_schema_version": intake_batch.schema_version,
        "intake_engine_id": intake_batch.engine_id,
        "intake_batch": intake_batch,
        "bindings": bindings,
        "dependency_count": len(dependency_by_id),
        "observation_count": intake_batch.observation_count,
        "unique_observation_count": intake_batch.unique_observation_count,
        "duplicate_observation_count": intake_batch.duplicate_observation_count,
        "state": STATE_READ_ONLY,
        "dependency_lineage_verified": True,
        "chain_lineage_verified": True,
        "certified_observation_lineage_verified": True,
        "deterministic_hashing_verified": intake_batch.deterministic_hashing_verified,
        "canonical_order_verified": intake_batch.canonical_order_verified,
        "duplicate_detection_verified": intake_batch.duplicate_detection_verified,
        "source_certification_verified": intake_batch.source_certification_verified,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "bridge_ready": True,
        "downstream_candidate_materialization_authorized": False,
        "read_only": True,
    }
    result = OracleMemoryCertifiedMarketBehaviorObservationIntakeBridge(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_market_behavior_observation_intake_bridge(result)
    return result


def verify_oracle_memory_certified_market_behavior_observation_intake_bridge(
    result: OracleMemoryCertifiedMarketBehaviorObservationIntakeBridge,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-065 certification hash mismatch")
    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-065 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-065 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-065 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-065 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-065 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-065 upstream engine lineage mismatch")
    if result.intake_schema_version != INTAKE_SCHEMA_VERSION:
        _reject("OML-065 intake schema lineage mismatch")
    if result.intake_engine_id != INTAKE_ENGINE_ID:
        _reject("OML-065 intake engine lineage mismatch")

    verify_oracle_memory_observation_intake_batch(result.intake_batch)

    if result.upstream_dependency_memory_hash != (
        result.intake_batch.upstream_memory_hash
    ):
        _reject("OML-065 dependency-to-intake lineage mismatch")
    if result.observation_count != len(result.bindings):
        _reject("OML-065 observation/binding count mismatch")
    if result.observation_count != result.intake_batch.observation_count:
        _reject("OML-065 observation count mismatch")

    observation_ids = tuple(
        item.observation_id for item in result.intake_batch.observations
    )
    binding_ids = tuple(item.observation_id for item in result.bindings)
    if observation_ids != binding_ids:
        _reject("OML-065 observation binding order mismatch")

    for binding in result.bindings:
        verify_oracle_memory_certified_market_behavior_observation_intake_binding(binding)
        if binding.upstream_certification_hash != (
            result.upstream_certification_hash
        ):
            _reject("OML-065 binding certification lineage mismatch")
        if binding.upstream_dependency_memory_hash != (
            result.upstream_dependency_memory_hash
        ):
            _reject("OML-065 binding dependency lineage mismatch")
        if binding.intake_batch_hash != result.intake_batch.batch_hash:
            _reject("OML-065 binding intake lineage mismatch")

    if not all((
        result.dependency_lineage_verified,
        result.chain_lineage_verified,
        result.certified_observation_lineage_verified,
        result.deterministic_hashing_verified,
        result.canonical_order_verified,
        result.duplicate_detection_verified,
        result.source_certification_verified,
        result.bridge_ready,
        result.read_only,
    )):
        _reject("OML-065 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-065 state invalid")
    if result.downstream_candidate_materialization_authorized:
        _reject("OML-065 candidate materialization must remain disabled")
    if any((
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )):
        _reject("OML-065 forbidden capability enabled")
    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_observation_intake_bridge import (
    OracleMemoryCertifiedMarketBehaviorObservationIntakeInvariantError,
    build_oracle_memory_certified_market_behavior_observation_intake_request,
    build_oracle_memory_certified_market_behavior_observation_intake_bridge,
    verify_oracle_memory_certified_market_behavior_observation_intake_bridge,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_intake_contract import (
    OracleMemoryObservationIntakeInvariantError,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except (
        OracleMemoryCertifiedMarketBehaviorObservationIntakeInvariantError,
        OracleMemoryObservationIntakeInvariantError,
    ):
        return
    raise AssertionError(f"tampered OML-065 {label} accepted")


def build_dependencies(root: Path):
    fixture = load_module(
        root
        / "test_oml_064_oracle_memory_certified_market_behavior_cross_market_dependency_memory.py",
        "oml_064_fixture_for_oml_065",
    )
    chains, certified_hashes = fixture.build_chains(root)
    chain_id = chains.chains.chain_memory.chains[0].chain_id

    from qseries_v2.oracle_memory.oracle_memory_certified_observation_cross_market_dependency_memory import (
        build_oracle_memory_certified_cross_market_observation_request,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_cross_market_dependency_memory import (
        build_oracle_memory_certified_market_behavior_cross_market_dependency_memory,
    )

    requests = (
        build_oracle_memory_certified_cross_market_observation_request(
            dependency_name=(
                "Certified market behavior leads Bitcoin repricing"
            ),
            chain_ids=(chain_id,),
            source_market_id="a" * 64,
            target_market_id="b" * 64,
            source_event_hash="c" * 64,
            target_event_hash="d" * 64,
            source_observed_at="2026-08-04T09:00:00-05:00",
            target_observed_at="2026-08-04T09:05:00-05:00",
            lag_seconds=300,
            certified_observation_hashes=(certified_hashes[0],),
            confidence=0.82,
            calibrated_probability=0.80,
            outcome_confirmed=True,
            dependency_supported=True,
        ),
        build_oracle_memory_certified_cross_market_observation_request(
            dependency_name=(
                "Certified market behavior leads Bitcoin repricing"
            ),
            chain_ids=(chain_id,),
            source_market_id="a" * 64,
            target_market_id="b" * 64,
            source_event_hash="e" * 64,
            target_event_hash="f" * 64,
            source_observed_at="2026-08-04T10:00:00-05:00",
            target_observed_at="2026-08-04T10:04:00-05:00",
            lag_seconds=240,
            certified_observation_hashes=(certified_hashes[-1],),
            confidence=0.80,
            calibrated_probability=0.75,
            outcome_confirmed=True,
            dependency_supported=True,
        ),
    )

    return (
        build_oracle_memory_certified_market_behavior_cross_market_dependency_memory(
            chains=chains,
            requests=requests,
        )
    )


def main() -> int:
    print("=" * 48)
    print(" OML-065 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR OBSERVATION INTAKE BRIDGE")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    dependencies = build_dependencies(root)
    dependency = dependencies.dependencies.dependency_memory.dependencies[0]

    request = build_oracle_memory_certified_market_behavior_observation_intake_request(
        dependency_id=dependency.dependency_id,
        domain_id=(
            "market_behavior_memory"
            if "market_behavior_memory" in MEMORY_DOMAINS
            else MEMORY_DOMAINS[0]
        ),
        entity_key="Bitcoin cross-market dependency",
        source_key="oracle-memory-oml-064",
        observed_at="2026-08-02T17:00:00-05:00",
        effective_at="2026-08-02T17:00:00-05:00",
        payload={
            "observation": (
                "A certified prediction-market dependency preceded "
                "crypto spot repricing."
            ),
            "observation_type": "cross_market_dependency",
        },
        confidence=0.80,
        uncertainty=0.20,
    )

    result = build_oracle_memory_certified_market_behavior_observation_intake_bridge(
        dependencies=dependencies,
        requests=(request,),
    )

    assert result.schema_version == "OML-065"
    assert result.engine_id == "OML-065"
    assert result.upstream_schema_version == "OML-064"
    assert result.upstream_engine_id == "OML-064"
    assert result.intake_schema_version == "OML-027"
    assert result.intake_engine_id == "OML-027"
    assert result.dependency_count == 1
    assert result.observation_count == 1
    assert result.unique_observation_count == 1
    assert result.duplicate_observation_count == 0

    observation = result.intake_batch.observations[0]
    binding = result.bindings[0]

    assert binding.dependency_id == dependency.dependency_id
    assert binding.dependency_hash == dependency.dependency_hash
    assert binding.observation_id == observation.observation_id
    assert binding.observation_hash == observation.observation_hash
    assert binding.upstream_certification_hash == dependencies.certification_hash
    assert binding.upstream_dependency_memory_hash == (
        dependencies.dependencies.dependency_memory.memory_hash
    )
    assert binding.intake_batch_hash == result.intake_batch.batch_hash
    assert observation.source_certification_hash == dependencies.certification_hash
    assert observation.evidence_hashes
    assert observation.parent_observation_hashes

    assert result.dependency_lineage_verified
    assert result.chain_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.deterministic_hashing_verified
    assert result.canonical_order_verified
    assert result.duplicate_detection_verified
    assert result.source_certification_verified
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.bridge_ready
    assert not result.downstream_candidate_materialization_authorized
    assert result.read_only

    replay = build_oracle_memory_certified_market_behavior_observation_intake_bridge(
        dependencies=dependencies,
        requests=(request,),
    )
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_observation_intake_bridge(result)

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_observation_intake_bridge(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_observation_intake_bridge(
            replace(result, downstream_candidate_materialization_authorized=True)
        ),
        "candidate materialization boundary",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_observation_intake_bridge(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-064 dependency memory consumed read-only")
    print("[PASS] Exact OML-038 dependency-memory dataclass passed directly")
    print("[PASS] Actual OML-027 observation and batch builders consumed")
    print("[PASS] Dependency, chain, causal, and observation lineage retained")
    print("[PASS] Source certification bound to OML-038 certification")
    print("[PASS] Deterministic intake observation generated")
    print("[PASS] Candidate materialization remained disabled")
    print("[PASS] Oracle Terminal separation preserved")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-065 bridges rejected")
    print("[DONE] OML-065 CERTIFIED MARKET-BEHAVIOR OBSERVATION INTAKE BRIDGE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_upstreams() -> None:
    required = (UPSTREAM, UPSTREAM_TEST, INTAKE_MODULE, INTAKE_TEST)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified upstream files missing: " + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_market_behavior_cross_market_dependency_memory"
    )
    intake_module = importlib.import_module(
        "qseries_v2.oracle_memory.oracle_memory_certified_observation_intake_contract"
    )

    expected_upstream = {
        "SCHEMA_VERSION": "OML-064",
        "ENGINE_ID": "OML-064",
        "POLICY_ID": (
            "oracle-memory."
            "certified-market-behavior-cross-market-dependency-memory.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-050",
        "UPSTREAM_ENGINE_ID": "OML-050",
        "DEPENDENCY_SCHEMA_VERSION": "OML-038",
        "DEPENDENCY_ENGINE_ID": "OML-038",
    }
    expected_intake = {
        "SCHEMA_VERSION": "OML-027",
        "ENGINE_ID": "OML-027",
        "POLICY_ID": "oracle-memory.certified-observation-intake-contract.v1",
        "UPSTREAM_SCHEMA_VERSION": "OML-026",
        "UPSTREAM_ENGINE_ID": "OML-026",
    }

    for name, value in expected_upstream.items():
        if getattr(upstream_module, name, None) != value:
            raise RuntimeError(f"Certified OML-064 {name} mismatch")
    for name, value in expected_intake.items():
        if getattr(intake_module, name, None) != value:
            raise RuntimeError(f"Certified OML-027 {name} mismatch")

    required_upstream_symbols = (
        "OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory",
        "verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory",
    )
    required_intake_symbols = (
        "OracleMemoryCertifiedObservation",
        "OracleMemoryObservationIntakeBatch",
        "build_oracle_memory_certified_observation",
        "build_oracle_memory_observation_intake_batch",
        "verify_oracle_memory_certified_observation",
        "verify_oracle_memory_observation_intake_batch",
        "OracleMemoryObservationIntakeInvariantError",
    )
    for module, names, label in (
        (upstream_module, required_upstream_symbols, "OML-064"),
        (intake_module, required_intake_symbols, "OML-027"),
    ):
        missing_names = [name for name in names if not hasattr(module, name)]
        if missing_names:
            raise RuntimeError(
                f"Certified {label} missing symbols: "
                + ", ".join(missing_names)
            )

    expected_builders = {
        "build_oracle_memory_certified_observation": {
            "observation_kind",
            "domain_id",
            "entity_key",
            "source_key",
            "observed_at",
            "effective_at",
            "payload",
            "evidence_hashes",
            "source_certification_hash",
            "parent_observation_hashes",
            "confidence",
            "uncertainty",
            "contradiction_count",
        },
        "build_oracle_memory_observation_intake_batch": {
            "cross_market_memory",
            "observations",
        },
    }
    for name, required_parameters in expected_builders.items():
        actual = set(inspect.signature(getattr(intake_module, name)).parameters)
        missing_parameters = sorted(required_parameters - actual)
        if missing_parameters:
            raise RuntimeError(
                f"Certified OML-027 {name} parameters missing: "
                + ", ".join(missing_parameters)
            )

    required_fields = {
        "schema_version",
        "engine_id",
        "certification_hash",
        "dependencies",
        "dependency_memory_ready",
        "downstream_market_behavior_authorized",
        "read_only",
    }
    actual_fields = set(
        upstream_module
        .OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory
        .__dataclass_fields__
    )
    missing_fields = sorted(required_fields - actual_fields)
    if missing_fields:
        raise RuntimeError(
            "Certified OML-064 dataclass fields missing: "
            + ", ".join(missing_fields)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-065 INSTALLER")
    print(" CERTIFIED MARKET-BEHAVIOR OBSERVATION INTAKE BRIDGE")
    print("=" * 48)
    print("[BOOT] Revision: EXACT_OML_051_WRAPPER_DEREFERENCE")

    try:
        validate_upstreams()
        print("[OK] Actual OML-064 dataclass and verifier inspected")
        print("[OK] Actual OML-027 builders and signatures inspected")

        for path, label in (
            (UPSTREAM_TEST, "OML-064"),
            (INTAKE_TEST, "OML-027"),
        ):
            run = subprocess.run(
                [sys.executable, str(path)],
                cwd=ROOT,
                check=False,
            )
            if run.returncode:
                raise RuntimeError(
                    f"{label} certification failed with exit code "
                    f"{run.returncode}"
                )

        tracked = {
            path: path.read_bytes()
            for path in (UPSTREAM, UPSTREAM_TEST, INTAKE_MODULE, INTAKE_TEST)
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_market_behavior_"
            "observation_intake_bridge import *"
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
                f"OML-065 test failed with exit code {completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Certified OML-064 production unchanged")
        print("[PASS] Certified OML-064 standalone test unchanged")
        print("[PASS] Certified OML-027 intake contract unchanged")
        print("[PASS] Exact OML-038 dependency-memory dataclass consumed directly")
        print("[PASS] OML-065 production fully replaced")
        print("[PASS] OML-065 standalone deterministic test installed")
        print("[PASS] Deterministic hashes and replay guarantees preserved")
        print("[PASS] Immutable certified lineage preserved")
        print("[PASS] Oracle Terminal separation preserved")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Runtime activation remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OML-065 CERTIFIED CROSS-MARKET "
            "OBSERVATION INTAKE BRIDGE INSTALLED"
        )
        return 0

    except (
        RuntimeError,
        SyntaxError,
        ImportError,
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
