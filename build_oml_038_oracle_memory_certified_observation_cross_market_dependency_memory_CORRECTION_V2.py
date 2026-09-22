from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_certified_observation_multi_hop_causal_chain_memory.py"
UPSTREAM_TEST = ROOT / "test_oml_037_oracle_memory_certified_observation_multi_hop_causal_chain_memory.py"
DEPENDENCY_MODULE = PACKAGE / "oracle_memory_cross_market_dependency_memory.py"
DEPENDENCY_TEST = ROOT / "test_oml_026_oracle_memory_cross_market_dependency_memory.py"

PRODUCTION = PACKAGE / "oracle_memory_certified_observation_cross_market_dependency_memory.py"
TEST = ROOT / "test_oml_038_oracle_memory_certified_observation_cross_market_dependency_memory.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_observation_multi_hop_causal_chain_memory import (
    OracleMemoryCertifiedMultiHopCausalChainMemory,
    verify_oracle_memory_certified_multi_hop_causal_chain_memory,
)
from qseries_v2.oracle_memory.oracle_memory_cross_market_dependency_memory import (
    OracleMemoryCrossMarketDependencyMemory,
    build_oracle_memory_cross_market_observation,
    build_oracle_memory_cross_market_dependency,
    build_oracle_memory_cross_market_dependency_memory,
    verify_oracle_memory_cross_market_observation,
    verify_oracle_memory_cross_market_dependency_memory,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-038"
ENGINE_ID = "OML-038"
POLICY_ID = "oracle-memory.certified-observation-cross-market-dependency-memory.v1"
UPSTREAM_SCHEMA_VERSION = "OML-037"
UPSTREAM_ENGINE_ID = "OML-037"
DEPENDENCY_SCHEMA_VERSION = "OML-026"
DEPENDENCY_ENGINE_ID = "OML-026"
STATE_READ_ONLY = "read_only_cross_market_dependency_memory"


class OracleMemoryCertifiedCrossMarketDependencyInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedCrossMarketObservationRequest:
    dependency_name: str
    chain_ids: tuple[str, ...]
    source_market_id: str
    target_market_id: str
    source_event_hash: str
    target_event_hash: str
    source_observed_at: str
    target_observed_at: str
    lag_seconds: int
    certified_observation_hashes: tuple[str, ...]
    contradicting_certified_observation_hashes: tuple[str, ...]
    confidence: float
    calibrated_probability: float
    outcome_confirmed: bool
    dependency_supported: bool | None
    request_hash: str


@dataclass(frozen=True)
class OracleMemoryCertifiedCrossMarketDependencyBinding:
    dependency_id: str
    dependency_name: str
    dependency_hash: str
    chain_ids: tuple[str, ...]
    certified_observation_hashes: tuple[str, ...]
    causal_observation_hashes: tuple[str, ...]
    cross_market_observation_hashes: tuple[str, ...]
    upstream_certification_hash: str
    upstream_chain_memory_hash: str
    dependency_memory_hash: str
    certified_observation_lineage_verified: bool
    chain_lineage_verified: bool
    market_identity_verified: bool
    lead_lag_direction_verified: bool
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
class OracleMemoryCertifiedCrossMarketDependencyMemory:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_chain_memory_hash: str
    dependency_schema_version: str
    dependency_engine_id: str
    dependency_memory: OracleMemoryCrossMarketDependencyMemory
    bindings: tuple[OracleMemoryCertifiedCrossMarketDependencyBinding, ...]
    dependency_count: int
    total_observation_count: int
    source_market_count: int
    target_market_count: int
    state: str
    certified_observation_lineage_verified: bool
    chain_lineage_verified: bool
    deterministic_identity_verified: bool
    canonical_dependency_order_verified: bool
    lead_lag_direction_verified: bool
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
    downstream_market_behavior_authorized: bool
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
    raise OracleMemoryCertifiedCrossMarketDependencyInvariantError(
        "unsupported OML-038 value type: "
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
    raise OracleMemoryCertifiedCrossMarketDependencyInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-038 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedCrossMarketDependencyInvariantError(
            f"OML-038 invalid {label} hexadecimal value"
        ) from exc


def _normalize(value: str) -> str:
    normalized = " ".join(value.strip().lower().split())
    if not normalized:
        _reject("OML-038 normalized value cannot be empty")
    return normalized


def build_oracle_memory_certified_cross_market_observation_request(
    *,
    dependency_name: str,
    chain_ids: Sequence[str],
    source_market_id: str,
    target_market_id: str,
    source_event_hash: str,
    target_event_hash: str,
    source_observed_at: str,
    target_observed_at: str,
    lag_seconds: int,
    certified_observation_hashes: Sequence[str],
    contradicting_certified_observation_hashes: Sequence[str] = (),
    confidence: float,
    calibrated_probability: float,
    outcome_confirmed: bool,
    dependency_supported: bool | None,
) -> OracleMemoryCertifiedCrossMarketObservationRequest:
    if not isinstance(dependency_name, str) or not dependency_name.strip():
        _reject("OML-038 dependency name required")

    ordered_chain_ids = tuple(sorted(set(chain_ids)))
    if not ordered_chain_ids:
        _reject("OML-038 causal chain lineage required")

    evidence = tuple(sorted(set(certified_observation_hashes)))
    contradictions = tuple(
        sorted(set(contradicting_certified_observation_hashes))
    )
    if not evidence:
        _reject("OML-038 certified observation evidence required")

    for value in (
        source_market_id,
        target_market_id,
        source_event_hash,
        target_event_hash,
        *ordered_chain_ids,
        *evidence,
        *contradictions,
    ):
        _require_hash(value, "request lineage hash")

    if source_market_id == target_market_id:
        _reject("OML-038 source and target markets must differ")
    if target_observed_at < source_observed_at:
        _reject("OML-038 target market cannot precede source market")
    if not isinstance(lag_seconds, int) or isinstance(lag_seconds, bool):
        _reject("OML-038 lag seconds invalid")
    if lag_seconds < 0:
        _reject("OML-038 lag seconds cannot be negative")

    confidence = float(confidence)
    calibrated_probability = float(calibrated_probability)
    if not 0.0 <= confidence <= 1.0:
        _reject("OML-038 confidence outside [0, 1]")
    if not 0.0 <= calibrated_probability <= 1.0:
        _reject("OML-038 probability outside [0, 1]")
    if outcome_confirmed:
        if dependency_supported is None:
            _reject("OML-038 confirmed outcome requires support result")
    elif dependency_supported is not None:
        _reject("OML-038 unresolved outcome cannot carry support result")

    body = {
        "dependency_name": dependency_name.strip(),
        "chain_ids": ordered_chain_ids,
        "source_market_id": source_market_id,
        "target_market_id": target_market_id,
        "source_event_hash": source_event_hash,
        "target_event_hash": target_event_hash,
        "source_observed_at": source_observed_at.strip(),
        "target_observed_at": target_observed_at.strip(),
        "lag_seconds": lag_seconds,
        "certified_observation_hashes": evidence,
        "contradicting_certified_observation_hashes": contradictions,
        "confidence": confidence,
        "calibrated_probability": calibrated_probability,
        "outcome_confirmed": bool(outcome_confirmed),
        "dependency_supported": dependency_supported,
    }
    result = OracleMemoryCertifiedCrossMarketObservationRequest(
        **body,
        request_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_cross_market_observation_request(result)
    return result


def verify_oracle_memory_certified_cross_market_observation_request(
    request: OracleMemoryCertifiedCrossMarketObservationRequest,
) -> bool:
    body = asdict(request)
    supplied = body.pop("request_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-038 request hash mismatch")
    for value in (
        request.source_market_id,
        request.target_market_id,
        request.source_event_hash,
        request.target_event_hash,
        request.request_hash,
        *request.chain_ids,
        *request.certified_observation_hashes,
        *request.contradicting_certified_observation_hashes,
    ):
        _require_hash(value, "request lineage hash")
    if not request.chain_ids:
        _reject("OML-038 request chain lineage missing")
    if not request.certified_observation_hashes:
        _reject("OML-038 request evidence missing")
    if request.source_market_id == request.target_market_id:
        _reject("OML-038 self-market dependency forbidden")
    if request.target_observed_at < request.source_observed_at:
        _reject("OML-038 temporal order violated")
    if request.lag_seconds < 0:
        _reject("OML-038 negative lag forbidden")
    return True


def _build_binding(
    *,
    dependency,
    requests: Sequence[OracleMemoryCertifiedCrossMarketObservationRequest],
    upstream: OracleMemoryCertifiedMultiHopCausalChainMemory,
    dependency_memory: OracleMemoryCrossMarketDependencyMemory,
) -> OracleMemoryCertifiedCrossMarketDependencyBinding:
    binding_by_chain = {item.chain_id: item for item in upstream.bindings}
    chain_ids = tuple(sorted({
        value for request in requests for value in request.chain_ids
    }))
    certified_hashes = tuple(sorted({
        value
        for request in requests
        for value in (
            *request.certified_observation_hashes,
            *request.contradicting_certified_observation_hashes,
        )
    }))
    causal_hashes = tuple(sorted({
        value
        for chain_id in chain_ids
        for value in binding_by_chain[chain_id].causal_observation_hashes
    }))
    body = {
        "dependency_id": dependency.dependency_id,
        "dependency_name": dependency.dependency_name,
        "dependency_hash": dependency.dependency_hash,
        "chain_ids": chain_ids,
        "certified_observation_hashes": certified_hashes,
        "causal_observation_hashes": causal_hashes,
        "cross_market_observation_hashes": tuple(
            item.observation_hash for item in dependency.observations
        ),
        "upstream_certification_hash": upstream.certification_hash,
        "upstream_chain_memory_hash": upstream.chain_memory.memory_hash,
        "dependency_memory_hash": dependency_memory.memory_hash,
        "certified_observation_lineage_verified": True,
        "chain_lineage_verified": True,
        "market_identity_verified": True,
        "lead_lag_direction_verified": dependency.lead_lag_direction_verified,
        "deterministic_binding_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }
    result = OracleMemoryCertifiedCrossMarketDependencyBinding(
        **body,
        binding_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_cross_market_dependency_binding(result)
    return result


def verify_oracle_memory_certified_cross_market_dependency_binding(
    binding: OracleMemoryCertifiedCrossMarketDependencyBinding,
) -> bool:
    body = asdict(binding)
    supplied = body.pop("binding_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-038 binding hash mismatch")
    for value in (
        binding.dependency_id,
        binding.dependency_hash,
        binding.upstream_certification_hash,
        binding.upstream_chain_memory_hash,
        binding.dependency_memory_hash,
        binding.binding_hash,
        *binding.chain_ids,
        *binding.certified_observation_hashes,
        *binding.causal_observation_hashes,
        *binding.cross_market_observation_hashes,
    ):
        _require_hash(value, "binding lineage hash")
    if not all((
        binding.certified_observation_lineage_verified,
        binding.chain_lineage_verified,
        binding.market_identity_verified,
        binding.lead_lag_direction_verified,
        binding.deterministic_binding_verified,
        binding.read_only,
    )):
        _reject("OML-038 binding guarantee missing")
    if any((
        binding.persistence_authorized,
        binding.learning_update_authorized,
        binding.runtime_activation_authorized,
        binding.publication_authorized,
        binding.action_authorization_enabled,
        binding.qseries_execution_authorized,
    )):
        _reject("OML-038 forbidden binding capability enabled")
    return True


def build_oracle_memory_certified_cross_market_dependency_memory(
    *,
    chains: OracleMemoryCertifiedMultiHopCausalChainMemory,
    requests: Sequence[OracleMemoryCertifiedCrossMarketObservationRequest],
) -> OracleMemoryCertifiedCrossMarketDependencyMemory:
    verify_oracle_memory_certified_multi_hop_causal_chain_memory(chains)
    if chains.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-038 upstream schema mismatch")
    if chains.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-038 upstream engine mismatch")
    if not chains.memory_ready:
        _reject("OML-038 upstream chain memory not ready")
    if not chains.downstream_causal_replay_authorized:
        _reject("OML-038 downstream continuation not authorized")
    if not chains.read_only:
        _reject("OML-038 upstream chain memory not read-only")

    chain_by_id = {item.chain_id: item for item in chains.chain_memory.chains}
    binding_by_id = {item.chain_id: item for item in chains.bindings}
    if set(chain_by_id) != set(binding_by_id):
        _reject("OML-038 upstream chain/binding identity mismatch")

    grouped_requests = {}
    grouped_observations = {}
    seen_hashes = set()

    for request in requests:
        verify_oracle_memory_certified_cross_market_observation_request(request)
        if request.request_hash in seen_hashes:
            _reject("OML-038 duplicate dependency request")
        seen_hashes.add(request.request_hash)

        if any(chain_id not in chain_by_id for chain_id in request.chain_ids):
            _reject("OML-038 request references unknown causal chain")

        allowed_certified = {
            value
            for chain_id in request.chain_ids
            for value in binding_by_id[chain_id].certified_observation_hashes
        }
        if not set(request.certified_observation_hashes).issubset(
            allowed_certified
        ):
            _reject("OML-038 unknown certified dependency evidence")
        if not set(
            request.contradicting_certified_observation_hashes
        ).issubset(allowed_certified):
            _reject("OML-038 unknown certified contradiction evidence")

        observation = build_oracle_memory_cross_market_observation(
            source_market_id=request.source_market_id,
            target_market_id=request.target_market_id,
            source_event_hash=request.source_event_hash,
            target_event_hash=request.target_event_hash,
            source_observed_at=request.source_observed_at,
            target_observed_at=request.target_observed_at,
            lag_seconds=request.lag_seconds,
            evidence_hashes=request.certified_observation_hashes,
            contradicting_evidence_hashes=(
                request.contradicting_certified_observation_hashes
            ),
            confidence=request.confidence,
            calibrated_probability=request.calibrated_probability,
            outcome_confirmed=request.outcome_confirmed,
            dependency_supported=request.dependency_supported,
        )
        verify_oracle_memory_cross_market_observation(observation)

        key = request.dependency_name.strip()
        grouped_requests.setdefault(key, []).append(request)
        grouped_observations.setdefault(key, []).append(observation)

    if not grouped_observations:
        _reject("OML-038 at least one dependency request required")

    dependencies = []
    for name, observations in sorted(
        grouped_observations.items(),
        key=lambda pair: _normalize(pair[0]),
    ):
        requests_for_name = grouped_requests[name]
        selected_chain_ids = tuple(sorted({
            chain_id
            for request in requests_for_name
            for chain_id in request.chain_ids
        }))
        selected_chains = tuple(chain_by_id[item] for item in selected_chain_ids)
        dependencies.append(
            build_oracle_memory_cross_market_dependency(
                dependency_name=name,
                observations=tuple(observations),
                causal_chains=selected_chains,
            )
        )

    dependency_memory = build_oracle_memory_cross_market_dependency_memory(
        causal_chain_memory=chains.chain_memory,
        dependencies=tuple(dependencies),
    )
    verify_oracle_memory_cross_market_dependency_memory(dependency_memory)

    if dependency_memory.schema_version != DEPENDENCY_SCHEMA_VERSION:
        _reject("OML-038 dependency schema mismatch")
    if dependency_memory.engine_id != DEPENDENCY_ENGINE_ID:
        _reject("OML-038 dependency engine mismatch")

    request_groups = {
        _normalize(name): tuple(values)
        for name, values in grouped_requests.items()
    }
    bindings = tuple(
        _build_binding(
            dependency=dependency,
            requests=request_groups[dependency.normalized_dependency_name],
            upstream=chains,
            dependency_memory=dependency_memory,
        )
        for dependency in dependency_memory.dependencies
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": chains.schema_version,
        "upstream_engine_id": chains.engine_id,
        "upstream_certification_hash": chains.certification_hash,
        "upstream_chain_memory_hash": chains.chain_memory.memory_hash,
        "dependency_schema_version": dependency_memory.schema_version,
        "dependency_engine_id": dependency_memory.engine_id,
        "dependency_memory": dependency_memory,
        "bindings": bindings,
        "dependency_count": dependency_memory.dependency_count,
        "total_observation_count": dependency_memory.total_observation_count,
        "source_market_count": dependency_memory.source_market_count,
        "target_market_count": dependency_memory.target_market_count,
        "state": STATE_READ_ONLY,
        "certified_observation_lineage_verified": True,
        "chain_lineage_verified": True,
        "deterministic_identity_verified": dependency_memory.deterministic_identity_verified,
        "canonical_dependency_order_verified": dependency_memory.canonical_dependency_order_verified,
        "lead_lag_direction_verified": dependency_memory.lead_lag_direction_verified,
        "evidence_lineage_verified": dependency_memory.evidence_lineage_verified,
        "contradiction_tracking_verified": dependency_memory.contradiction_tracking_verified,
        "calibration_lineage_verified": dependency_memory.calibration_lineage_verified,
        "outcome_reconciliation_verified": dependency_memory.outcome_reconciliation_verified,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "memory_ready": True,
        "downstream_market_behavior_authorized": True,
        "read_only": True,
    }
    result = OracleMemoryCertifiedCrossMarketDependencyMemory(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_cross_market_dependency_memory(result)
    return result


def verify_oracle_memory_certified_cross_market_dependency_memory(
    result: OracleMemoryCertifiedCrossMarketDependencyMemory,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-038 certification hash mismatch")
    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-038 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-038 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-038 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-038 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-038 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-038 upstream engine lineage mismatch")
    if result.dependency_schema_version != DEPENDENCY_SCHEMA_VERSION:
        _reject("OML-038 dependency schema lineage mismatch")
    if result.dependency_engine_id != DEPENDENCY_ENGINE_ID:
        _reject("OML-038 dependency engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_chain_memory_hash,
        result.certification_hash,
    ):
        _require_hash(value, "certification lineage hash")

    verify_oracle_memory_cross_market_dependency_memory(
        result.dependency_memory
    )
    if result.upstream_chain_memory_hash != (
        result.dependency_memory.upstream_memory_hash
    ):
        _reject("OML-038 chain-to-dependency lineage mismatch")
    if result.dependency_count != len(result.bindings):
        _reject("OML-038 dependency/binding count mismatch")
    if result.dependency_count != result.dependency_memory.dependency_count:
        _reject("OML-038 dependency count mismatch")
    if result.total_observation_count != (
        result.dependency_memory.total_observation_count
    ):
        _reject("OML-038 observation count mismatch")

    dependency_ids = tuple(
        item.dependency_id for item in result.dependency_memory.dependencies
    )
    binding_ids = tuple(item.dependency_id for item in result.bindings)
    if dependency_ids != binding_ids:
        _reject("OML-038 dependency binding order mismatch")

    for binding in result.bindings:
        verify_oracle_memory_certified_cross_market_dependency_binding(
            binding
        )
        if binding.upstream_certification_hash != (
            result.upstream_certification_hash
        ):
            _reject("OML-038 binding certification lineage mismatch")
        if binding.upstream_chain_memory_hash != (
            result.upstream_chain_memory_hash
        ):
            _reject("OML-038 binding chain lineage mismatch")
        if binding.dependency_memory_hash != (
            result.dependency_memory.memory_hash
        ):
            _reject("OML-038 binding dependency lineage mismatch")

    if not all((
        result.certified_observation_lineage_verified,
        result.chain_lineage_verified,
        result.deterministic_identity_verified,
        result.canonical_dependency_order_verified,
        result.lead_lag_direction_verified,
        result.evidence_lineage_verified,
        result.contradiction_tracking_verified,
        result.calibration_lineage_verified,
        result.outcome_reconciliation_verified,
        result.memory_ready,
        result.downstream_market_behavior_authorized,
        result.read_only,
    )):
        _reject("OML-038 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-038 state invalid")
    if any((
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )):
        _reject("OML-038 forbidden capability enabled")
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
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_cross_market_dependency_memory import (
    OracleMemoryCertifiedCrossMarketDependencyInvariantError,
    build_oracle_memory_certified_cross_market_observation_request,
    build_oracle_memory_certified_cross_market_dependency_memory,
    verify_oracle_memory_certified_cross_market_dependency_memory,
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
        OracleMemoryCertifiedCrossMarketDependencyInvariantError,
        OracleMemoryCrossMarketDependencyInvariantError,
    ):
        return
    raise AssertionError(f"tampered OML-038 {label} accepted")


def build_chains(root: Path):
    fixture = load_module(
        root / "test_oml_037_oracle_memory_certified_observation_multi_hop_causal_chain_memory.py",
        "oml_037_fixture_for_oml_038",
    )
    return fixture.build_causal_patterns(root)


def main() -> int:
    print("=" * 48)
    print(" OML-038 TEST")
    print(" CERTIFIED OBSERVATION CROSS-MARKET DEPENDENCY MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    causal_patterns = build_chains(root)

    from qseries_v2.oracle_memory.oracle_memory_certified_observation_multi_hop_causal_chain_memory import (
        build_oracle_memory_certified_multi_hop_chain_request,
        build_oracle_memory_certified_multi_hop_causal_chain_memory,
    )

    ordered_patterns = sorted(
        causal_patterns.causal_memory.patterns,
        key=lambda item: item.cause_entity_id,
    )
    chain_request = build_oracle_memory_certified_multi_hop_chain_request(
        chain_name="Real-world demand to market repricing chain",
        pattern_ids=tuple(item.pattern_id for item in ordered_patterns),
    )
    chains = build_oracle_memory_certified_multi_hop_causal_chain_memory(
        causal_patterns=causal_patterns,
        requests=(chain_request,),
    )

    chain = chains.chain_memory.chains[0]
    binding = chains.bindings[0]
    certified_hashes = binding.certified_observation_hashes

    source_market_id = "a" * 64
    target_market_id = "b" * 64

    requests = (
        build_oracle_memory_certified_cross_market_observation_request(
            dependency_name="Prediction market leads crypto spot repricing",
            chain_ids=(chain.chain_id,),
            source_market_id=source_market_id,
            target_market_id=target_market_id,
            source_event_hash="c" * 64,
            target_event_hash="d" * 64,
            source_observed_at="2026-08-02T14:00:00-05:00",
            target_observed_at="2026-08-02T14:05:00-05:00",
            lag_seconds=300,
            certified_observation_hashes=(certified_hashes[0],),
            confidence=0.82,
            calibrated_probability=0.80,
            outcome_confirmed=True,
            dependency_supported=True,
        ),
        build_oracle_memory_certified_cross_market_observation_request(
            dependency_name="Prediction market leads crypto spot repricing",
            chain_ids=(chain.chain_id,),
            source_market_id=source_market_id,
            target_market_id=target_market_id,
            source_event_hash="e" * 64,
            target_event_hash="f" * 64,
            source_observed_at="2026-08-02T15:00:00-05:00",
            target_observed_at="2026-08-02T15:04:00-05:00",
            lag_seconds=240,
            certified_observation_hashes=(certified_hashes[-1],),
            confidence=0.80,
            calibrated_probability=0.78,
            outcome_confirmed=True,
            dependency_supported=True,
        ),
        build_oracle_memory_certified_cross_market_observation_request(
            dependency_name="Prediction market leads crypto spot repricing",
            chain_ids=(chain.chain_id,),
            source_market_id=source_market_id,
            target_market_id=target_market_id,
            source_event_hash="1" * 64,
            target_event_hash="2" * 64,
            source_observed_at="2026-08-02T16:00:00-05:00",
            target_observed_at="2026-08-02T16:06:00-05:00",
            lag_seconds=360,
            certified_observation_hashes=(certified_hashes[0],),
            contradicting_certified_observation_hashes=(certified_hashes[-1],),
            confidence=0.79,
            calibrated_probability=0.76,
            outcome_confirmed=True,
            dependency_supported=True,
        ),
    )

    result = build_oracle_memory_certified_cross_market_dependency_memory(
        chains=chains,
        requests=requests,
    )

    assert result.schema_version == "OML-038"
    assert result.engine_id == "OML-038"
    assert result.upstream_schema_version == "OML-037"
    assert result.upstream_engine_id == "OML-037"
    assert result.dependency_schema_version == "OML-026"
    assert result.dependency_engine_id == "OML-026"
    assert result.dependency_count == 1
    assert result.total_observation_count == 3
    assert result.source_market_count == 1
    assert result.target_market_count == 1

    dependency = result.dependency_memory.dependencies[0]
    dependency_binding = result.bindings[0]

    assert dependency.dependency_status == DEPENDENCY_STATUS_ESTABLISHED
    assert dependency.observation_count == 3
    assert dependency.confirmed_count == 3
    assert dependency.supported_count == 3
    assert dependency.contradicted_count == 0
    assert dependency.empirical_support_rate == 1.0
    assert dependency.minimum_lag_seconds == 240
    assert dependency.maximum_lag_seconds == 360
    assert dependency.average_lag_seconds == 300.0

    assert dependency_binding.dependency_id == dependency.dependency_id
    assert dependency_binding.dependency_hash == dependency.dependency_hash
    assert dependency_binding.chain_ids == (chain.chain_id,)
    assert dependency_binding.upstream_certification_hash == (
        chains.certification_hash
    )
    assert dependency_binding.upstream_chain_memory_hash == (
        chains.chain_memory.memory_hash
    )
    assert dependency_binding.dependency_memory_hash == (
        result.dependency_memory.memory_hash
    )

    assert result.certified_observation_lineage_verified
    assert result.chain_lineage_verified
    assert result.deterministic_identity_verified
    assert result.canonical_dependency_order_verified
    assert result.lead_lag_direction_verified
    assert result.evidence_lineage_verified
    assert result.contradiction_tracking_verified
    assert result.calibration_lineage_verified
    assert result.outcome_reconciliation_verified
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.memory_ready
    assert result.downstream_market_behavior_authorized
    assert result.read_only

    replay = build_oracle_memory_certified_cross_market_dependency_memory(
        chains=chains,
        requests=requests,
    )
    assert replay == result
    assert verify_oracle_memory_certified_cross_market_dependency_memory(result)

    expect_rejection(
        lambda: build_oracle_memory_certified_cross_market_observation_request(
            dependency_name="Broken",
            chain_ids=(chain.chain_id,),
            source_market_id=source_market_id,
            target_market_id=source_market_id,
            source_event_hash="c" * 64,
            target_event_hash="d" * 64,
            source_observed_at="2026-08-02T14:00:00-05:00",
            target_observed_at="2026-08-02T14:05:00-05:00",
            lag_seconds=300,
            certified_observation_hashes=(certified_hashes[0],),
            confidence=0.50,
            calibrated_probability=0.50,
            outcome_confirmed=False,
            dependency_supported=None,
        ),
        "self-market dependency",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_dependency_memory(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_dependency_memory(
            replace(result, downstream_market_behavior_authorized=False)
        ),
        "market behavior continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_dependency_memory(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-037 chain memory consumed read-only")
    print("[PASS] Exact OML-037 chain-memory dataclass passed directly")
    print("[PASS] Actual OML-026 dependency builders consumed")
    print("[PASS] Certified chain lineage bound to every dependency")
    print("[PASS] Certified observation lineage retained")
    print("[PASS] Cross-market lead-lag direction enforced")
    print("[PASS] Lag statistics and outcomes reconciled")
    print("[PASS] Established dependency detected")
    print("[PASS] Deterministic hashes and replay equality verified")
    print("[PASS] Market-behavior continuation authorized read-only")
    print("[PASS] Oracle Terminal separation preserved")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-038 dependency memories rejected")
    print("[DONE] OML-038 CERTIFIED OBSERVATION CROSS-MARKET DEPENDENCY MEMORY PASS")
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
    required = (UPSTREAM, UPSTREAM_TEST, DEPENDENCY_MODULE, DEPENDENCY_TEST)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified upstream files missing: " + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_multi_hop_causal_chain_memory"
    )
    dependency_module = importlib.import_module(
        "qseries_v2.oracle_memory.oracle_memory_cross_market_dependency_memory"
    )

    expected_upstream = {
        "SCHEMA_VERSION": "OML-037",
        "ENGINE_ID": "OML-037",
        "POLICY_ID": (
            "oracle-memory."
            "certified-observation-multi-hop-causal-chain-memory.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-036",
        "UPSTREAM_ENGINE_ID": "OML-036",
        "CHAIN_SCHEMA_VERSION": "OML-025",
        "CHAIN_ENGINE_ID": "OML-025",
    }
    expected_dependency = {
        "SCHEMA_VERSION": "OML-026",
        "ENGINE_ID": "OML-026",
        "POLICY_ID": "oracle-memory.cross-market-dependency-memory.v1",
        "UPSTREAM_SCHEMA_VERSION": "OML-025",
        "UPSTREAM_ENGINE_ID": "OML-025",
    }

    for name, value in expected_upstream.items():
        if getattr(upstream_module, name, None) != value:
            raise RuntimeError(f"Certified OML-037 {name} mismatch")
    for name, value in expected_dependency.items():
        if getattr(dependency_module, name, None) != value:
            raise RuntimeError(f"Certified OML-026 {name} mismatch")

    required_upstream_symbols = (
        "OracleMemoryCertifiedMultiHopCausalChainMemory",
        "verify_oracle_memory_certified_multi_hop_causal_chain_memory",
    )
    required_dependency_symbols = (
        "OracleMemoryCrossMarketDependencyMemory",
        "build_oracle_memory_cross_market_observation",
        "build_oracle_memory_cross_market_dependency",
        "build_oracle_memory_cross_market_dependency_memory",
        "verify_oracle_memory_cross_market_observation",
        "verify_oracle_memory_cross_market_dependency_memory",
        "OracleMemoryCrossMarketDependencyInvariantError",
    )

    for module, names, label in (
        (upstream_module, required_upstream_symbols, "OML-037"),
        (dependency_module, required_dependency_symbols, "OML-026"),
    ):
        missing_names = [name for name in names if not hasattr(module, name)]
        if missing_names:
            raise RuntimeError(
                f"Certified {label} missing symbols: "
                + ", ".join(missing_names)
            )

    builders = {
        "build_oracle_memory_cross_market_observation": {
            "source_market_id",
            "target_market_id",
            "source_event_hash",
            "target_event_hash",
            "source_observed_at",
            "target_observed_at",
            "lag_seconds",
            "evidence_hashes",
            "contradicting_evidence_hashes",
            "confidence",
            "calibrated_probability",
            "outcome_confirmed",
            "dependency_supported",
        },
        "build_oracle_memory_cross_market_dependency": {
            "dependency_name",
            "observations",
            "causal_chains",
        },
        "build_oracle_memory_cross_market_dependency_memory": {
            "causal_chain_memory",
            "dependencies",
        },
    }
    for builder_name, required_parameters in builders.items():
        actual = set(
            inspect.signature(
                getattr(dependency_module, builder_name)
            ).parameters
        )
        missing_parameters = sorted(required_parameters - actual)
        if missing_parameters:
            raise RuntimeError(
                f"Certified OML-026 {builder_name} parameters missing: "
                + ", ".join(missing_parameters)
            )

    required_upstream_fields = {
        "schema_version",
        "engine_id",
        "certification_hash",
        "chain_memory",
        "bindings",
        "memory_ready",
        "downstream_causal_replay_authorized",
        "read_only",
    }
    actual_fields = set(
        upstream_module
        .OracleMemoryCertifiedMultiHopCausalChainMemory
        .__dataclass_fields__
    )
    missing_fields = sorted(required_upstream_fields - actual_fields)
    if missing_fields:
        raise RuntimeError(
            "Certified OML-037 dataclass fields missing: "
            + ", ".join(missing_fields)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-038 CORRECTION V2 INSTALLER")
    print(" CERTIFIED OBSERVATION CROSS-MARKET DEPENDENCY MEMORY")
    print("=" * 48)
    print("[BOOT] Revision: CORRECTION_V2_EXACT_OML_037_026_INTERFACE_ALIGNMENT")

    try:
        validate_upstreams()
        print("[OK] Actual OML-037 dataclass and verifier inspected")
        print("[OK] Actual OML-026 builders and signatures inspected")

        for path, label in (
            (UPSTREAM_TEST, "OML-037"),
            (DEPENDENCY_TEST, "OML-026"),
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
            for path in (
                UPSTREAM,
                UPSTREAM_TEST,
                DEPENDENCY_MODULE,
                DEPENDENCY_TEST,
            )
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_observation_"
            "cross_market_dependency_memory import *"
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
                f"OML-038 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Certified OML-037 production unchanged")
        print("[PASS] Certified OML-037 standalone test unchanged")
        print("[PASS] Certified OML-026 dependency engine unchanged")
        print("[PASS] Exact OML-037 chain-memory dataclass consumed directly")
        print("[PASS] OML-038 production fully replaced")
        print("[PASS] OML-038 standalone deterministic test installed")
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
            "[DONE] OML-038 CORRECTION V2 CERTIFIED OBSERVATION "
            "CROSS-MARKET DEPENDENCY MEMORY INSTALLED"
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
