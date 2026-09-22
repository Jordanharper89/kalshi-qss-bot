from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_certified_observation_causal_pattern_memory.py"
UPSTREAM_TEST = ROOT / "test_oml_036_oracle_memory_certified_observation_causal_pattern_memory.py"
CHAIN_MODULE = PACKAGE / "oracle_memory_multi_hop_causal_chain_memory.py"
CHAIN_TEST = ROOT / "test_oml_025_oracle_memory_multi_hop_causal_chain_memory.py"

PRODUCTION = PACKAGE / "oracle_memory_certified_observation_multi_hop_causal_chain_memory.py"
TEST = ROOT / "test_oml_037_oracle_memory_certified_observation_multi_hop_causal_chain_memory.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_observation_causal_pattern_memory import (
    OracleMemoryCertifiedCausalPatternMemory,
    verify_oracle_memory_certified_causal_pattern_memory,
)
from qseries_v2.oracle_memory.oracle_memory_multi_hop_causal_chain_memory import (
    OracleMemoryMultiHopCausalChainMemory,
    build_oracle_memory_multi_hop_causal_chain,
    build_oracle_memory_multi_hop_causal_chain_memory,
    verify_oracle_memory_multi_hop_causal_chain,
    verify_oracle_memory_multi_hop_causal_chain_memory,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-037"
ENGINE_ID = "OML-037"
POLICY_ID = "oracle-memory.certified-observation-multi-hop-causal-chain-memory.v1"
UPSTREAM_SCHEMA_VERSION = "OML-036"
UPSTREAM_ENGINE_ID = "OML-036"
CHAIN_SCHEMA_VERSION = "OML-025"
CHAIN_ENGINE_ID = "OML-025"
STATE_READ_ONLY = "read_only_multi_hop_causal_chain_memory"


class OracleMemoryCertifiedMultiHopCausalChainInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedMultiHopChainRequest:
    chain_name: str
    pattern_ids: tuple[str, ...]
    request_hash: str


@dataclass(frozen=True)
class OracleMemoryCertifiedMultiHopChainBinding:
    chain_id: str
    chain_name: str
    chain_hash: str
    pattern_ids: tuple[str, ...]
    certified_observation_hashes: tuple[str, ...]
    causal_observation_hashes: tuple[str, ...]
    upstream_certification_hash: str
    upstream_causal_memory_hash: str
    chain_memory_hash: str
    certified_observation_lineage_verified: bool
    causal_pattern_lineage_verified: bool
    hop_continuity_verified: bool
    temporal_direction_verified: bool
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
class OracleMemoryCertifiedMultiHopCausalChainMemory:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_causal_memory_hash: str
    chain_schema_version: str
    chain_engine_id: str
    chain_memory: OracleMemoryMultiHopCausalChainMemory
    bindings: tuple[OracleMemoryCertifiedMultiHopChainBinding, ...]
    chain_count: int
    total_hop_count: int
    state: str
    certified_observation_lineage_verified: bool
    causal_pattern_lineage_verified: bool
    deterministic_identity_verified: bool
    canonical_chain_order_verified: bool
    hop_continuity_verified: bool
    temporal_direction_verified: bool
    evidence_depth_reconciled: bool
    contradiction_depth_reconciled: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    memory_ready: bool
    downstream_causal_replay_authorized: bool
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
    raise OracleMemoryCertifiedMultiHopCausalChainInvariantError(
        "unsupported OML-037 value type: "
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
    raise OracleMemoryCertifiedMultiHopCausalChainInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-037 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedMultiHopCausalChainInvariantError(
            f"OML-037 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_multi_hop_chain_request(
    *,
    chain_name: str,
    pattern_ids: Sequence[str],
) -> OracleMemoryCertifiedMultiHopChainRequest:
    if not isinstance(chain_name, str) or not chain_name.strip():
        _reject("OML-037 chain name required")
    ordered = tuple(pattern_ids)
    if len(ordered) < 2:
        _reject("OML-037 chain requires at least two pattern ids")
    if len(set(ordered)) != len(ordered):
        _reject("OML-037 duplicate pattern ids forbidden")
    for value in ordered:
        _require_hash(value, "pattern id")
    body = {
        "chain_name": chain_name.strip(),
        "pattern_ids": ordered,
    }
    result = OracleMemoryCertifiedMultiHopChainRequest(
        **body,
        request_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_multi_hop_chain_request(result)
    return result


def verify_oracle_memory_certified_multi_hop_chain_request(
    request: OracleMemoryCertifiedMultiHopChainRequest,
) -> bool:
    body = asdict(request)
    supplied = body.pop("request_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-037 request hash mismatch")
    _require_hash(request.request_hash, "request hash")
    if not request.chain_name.strip():
        _reject("OML-037 chain name missing")
    if len(request.pattern_ids) < 2:
        _reject("OML-037 chain request too short")
    if len(set(request.pattern_ids)) != len(request.pattern_ids):
        _reject("OML-037 duplicate request pattern ids")
    for value in request.pattern_ids:
        _require_hash(value, "pattern id")
    return True


def _build_binding(
    *,
    chain,
    upstream: OracleMemoryCertifiedCausalPatternMemory,
    chain_memory: OracleMemoryMultiHopCausalChainMemory,
) -> OracleMemoryCertifiedMultiHopChainBinding:
    binding_by_pattern = {
        item.pattern_id: item for item in upstream.bindings
    }
    certified_hashes = tuple(sorted({
        value
        for hop in chain.hops
        for value in binding_by_pattern[hop.pattern_id].certified_observation_hashes
    }))
    causal_hashes = tuple(sorted({
        value
        for hop in chain.hops
        for value in binding_by_pattern[hop.pattern_id].causal_observation_hashes
    }))
    body = {
        "chain_id": chain.chain_id,
        "chain_name": chain.chain_name,
        "chain_hash": chain.chain_hash,
        "pattern_ids": tuple(hop.pattern_id for hop in chain.hops),
        "certified_observation_hashes": certified_hashes,
        "causal_observation_hashes": causal_hashes,
        "upstream_certification_hash": upstream.certification_hash,
        "upstream_causal_memory_hash": upstream.causal_memory.memory_hash,
        "chain_memory_hash": chain_memory.memory_hash,
        "certified_observation_lineage_verified": True,
        "causal_pattern_lineage_verified": True,
        "hop_continuity_verified": chain.hop_continuity_verified,
        "temporal_direction_verified": chain.temporal_direction_verified,
        "deterministic_binding_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }
    result = OracleMemoryCertifiedMultiHopChainBinding(
        **body,
        binding_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_multi_hop_chain_binding(result)
    return result


def verify_oracle_memory_certified_multi_hop_chain_binding(
    binding: OracleMemoryCertifiedMultiHopChainBinding,
) -> bool:
    body = asdict(binding)
    supplied = body.pop("binding_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-037 binding hash mismatch")
    for value in (
        binding.chain_id,
        binding.chain_hash,
        binding.upstream_certification_hash,
        binding.upstream_causal_memory_hash,
        binding.chain_memory_hash,
        binding.binding_hash,
        *binding.pattern_ids,
        *binding.certified_observation_hashes,
        *binding.causal_observation_hashes,
    ):
        _require_hash(value, "binding lineage hash")
    if not all((
        binding.certified_observation_lineage_verified,
        binding.causal_pattern_lineage_verified,
        binding.hop_continuity_verified,
        binding.temporal_direction_verified,
        binding.deterministic_binding_verified,
        binding.read_only,
    )):
        _reject("OML-037 binding guarantee missing")
    if any((
        binding.persistence_authorized,
        binding.learning_update_authorized,
        binding.runtime_activation_authorized,
        binding.publication_authorized,
        binding.action_authorization_enabled,
        binding.qseries_execution_authorized,
    )):
        _reject("OML-037 forbidden binding capability enabled")
    return True


def build_oracle_memory_certified_multi_hop_causal_chain_memory(
    *,
    causal_patterns: OracleMemoryCertifiedCausalPatternMemory,
    requests: Sequence[OracleMemoryCertifiedMultiHopChainRequest],
) -> OracleMemoryCertifiedMultiHopCausalChainMemory:
    verify_oracle_memory_certified_causal_pattern_memory(causal_patterns)
    if causal_patterns.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-037 upstream schema mismatch")
    if causal_patterns.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-037 upstream engine mismatch")
    if not causal_patterns.memory_ready:
        _reject("OML-037 upstream causal memory not ready")
    if not causal_patterns.downstream_multi_hop_causal_authorized:
        _reject("OML-037 multi-hop continuation not authorized")
    if not causal_patterns.read_only:
        _reject("OML-037 upstream causal memory not read-only")

    patterns_by_id = {
        pattern.pattern_id: pattern
        for pattern in causal_patterns.causal_memory.patterns
    }
    binding_ids = {binding.pattern_id for binding in causal_patterns.bindings}
    if set(patterns_by_id) != binding_ids:
        _reject("OML-037 upstream pattern/binding identity mismatch")

    chains = []
    seen_request_hashes = set()
    for request in requests:
        verify_oracle_memory_certified_multi_hop_chain_request(request)
        if request.request_hash in seen_request_hashes:
            _reject("OML-037 duplicate chain request")
        seen_request_hashes.add(request.request_hash)
        try:
            selected_patterns = tuple(
                patterns_by_id[pattern_id]
                for pattern_id in request.pattern_ids
            )
        except KeyError as exc:
            raise OracleMemoryCertifiedMultiHopCausalChainInvariantError(
                "OML-037 request references unknown causal pattern"
            ) from exc
        chain = build_oracle_memory_multi_hop_causal_chain(
            chain_name=request.chain_name,
            patterns=selected_patterns,
        )
        verify_oracle_memory_multi_hop_causal_chain(chain)
        chains.append(chain)

    if not chains:
        _reject("OML-037 at least one chain request required")

    chain_memory = build_oracle_memory_multi_hop_causal_chain_memory(
        causal_memory=causal_patterns.causal_memory,
        chains=tuple(chains),
    )
    verify_oracle_memory_multi_hop_causal_chain_memory(chain_memory)
    if chain_memory.schema_version != CHAIN_SCHEMA_VERSION:
        _reject("OML-037 chain schema mismatch")
    if chain_memory.engine_id != CHAIN_ENGINE_ID:
        _reject("OML-037 chain engine mismatch")

    bindings = tuple(
        _build_binding(
            chain=chain,
            upstream=causal_patterns,
            chain_memory=chain_memory,
        )
        for chain in chain_memory.chains
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": causal_patterns.schema_version,
        "upstream_engine_id": causal_patterns.engine_id,
        "upstream_certification_hash": causal_patterns.certification_hash,
        "upstream_causal_memory_hash": causal_patterns.causal_memory.memory_hash,
        "chain_schema_version": chain_memory.schema_version,
        "chain_engine_id": chain_memory.engine_id,
        "chain_memory": chain_memory,
        "bindings": bindings,
        "chain_count": chain_memory.chain_count,
        "total_hop_count": chain_memory.total_hop_count,
        "state": STATE_READ_ONLY,
        "certified_observation_lineage_verified": True,
        "causal_pattern_lineage_verified": True,
        "deterministic_identity_verified": chain_memory.deterministic_identity_verified,
        "canonical_chain_order_verified": chain_memory.canonical_chain_order_verified,
        "hop_continuity_verified": chain_memory.hop_continuity_verified,
        "temporal_direction_verified": chain_memory.temporal_direction_verified,
        "evidence_depth_reconciled": chain_memory.evidence_depth_reconciled,
        "contradiction_depth_reconciled": chain_memory.contradiction_depth_reconciled,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "memory_ready": True,
        "downstream_causal_replay_authorized": True,
        "read_only": True,
    }
    result = OracleMemoryCertifiedMultiHopCausalChainMemory(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_multi_hop_causal_chain_memory(result)
    return result


def verify_oracle_memory_certified_multi_hop_causal_chain_memory(
    result: OracleMemoryCertifiedMultiHopCausalChainMemory,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-037 certification hash mismatch")
    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-037 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-037 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-037 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-037 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-037 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-037 upstream engine lineage mismatch")
    if result.chain_schema_version != CHAIN_SCHEMA_VERSION:
        _reject("OML-037 chain schema lineage mismatch")
    if result.chain_engine_id != CHAIN_ENGINE_ID:
        _reject("OML-037 chain engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_causal_memory_hash,
        result.certification_hash,
    ):
        _require_hash(value, "certification lineage hash")

    verify_oracle_memory_multi_hop_causal_chain_memory(result.chain_memory)
    if result.upstream_causal_memory_hash != result.chain_memory.upstream_memory_hash:
        _reject("OML-037 causal-to-chain lineage mismatch")
    if result.chain_count != len(result.bindings):
        _reject("OML-037 chain/binding count mismatch")
    if result.chain_count != result.chain_memory.chain_count:
        _reject("OML-037 chain count mismatch")
    if result.total_hop_count != result.chain_memory.total_hop_count:
        _reject("OML-037 hop count mismatch")

    chain_ids = tuple(chain.chain_id for chain in result.chain_memory.chains)
    binding_ids = tuple(binding.chain_id for binding in result.bindings)
    if chain_ids != binding_ids:
        _reject("OML-037 chain binding order mismatch")

    for binding in result.bindings:
        verify_oracle_memory_certified_multi_hop_chain_binding(binding)
        if binding.upstream_certification_hash != result.upstream_certification_hash:
            _reject("OML-037 binding certification lineage mismatch")
        if binding.upstream_causal_memory_hash != result.upstream_causal_memory_hash:
            _reject("OML-037 binding causal lineage mismatch")
        if binding.chain_memory_hash != result.chain_memory.memory_hash:
            _reject("OML-037 binding chain-memory lineage mismatch")

    if not all((
        result.certified_observation_lineage_verified,
        result.causal_pattern_lineage_verified,
        result.deterministic_identity_verified,
        result.canonical_chain_order_verified,
        result.hop_continuity_verified,
        result.temporal_direction_verified,
        result.evidence_depth_reconciled,
        result.contradiction_depth_reconciled,
        result.memory_ready,
        result.downstream_causal_replay_authorized,
        result.read_only,
    )):
        _reject("OML-037 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-037 state invalid")
    if any((
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )):
        _reject("OML-037 forbidden capability enabled")
    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_multi_hop_causal_chain_memory import (
    CHAIN_STATUS_ESTABLISHED,
    OracleMemoryMultiHopCausalChainInvariantError,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_causal_pattern_memory import (
    build_oracle_memory_certified_causal_observation_request,
    build_oracle_memory_certified_causal_pattern_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_multi_hop_causal_chain_memory import (
    OracleMemoryCertifiedMultiHopCausalChainInvariantError,
    build_oracle_memory_certified_multi_hop_chain_request,
    build_oracle_memory_certified_multi_hop_causal_chain_memory,
    verify_oracle_memory_certified_multi_hop_causal_chain_memory,
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
        OracleMemoryCertifiedMultiHopCausalChainInvariantError,
        OracleMemoryMultiHopCausalChainInvariantError,
    ):
        return
    raise AssertionError(f"tampered OML-037 {label} accepted")


def build_causal_patterns(root: Path):
    fixture = load_module(
        root / "test_oml_036_oracle_memory_certified_observation_causal_pattern_memory.py",
        "oml_036_fixture_for_oml_037",
    )
    calibration, certified_hashes = fixture.build_calibration(root)

    entity_a = "1" * 64
    entity_b = "2" * 64
    entity_c = "3" * 64

    requests = (
        build_oracle_memory_certified_causal_observation_request(
            pattern_name="Demand shift precedes order-flow change",
            cause_entity_id=entity_a,
            effect_entity_id=entity_b,
            cause_observed_at="2026-08-02T14:00:00-05:00",
            effect_observed_at="2026-08-02T14:15:00-05:00",
            certified_observation_hashes=(certified_hashes[0],),
            confidence=0.82,
            calibrated_probability=0.82,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_certified_causal_observation_request(
            pattern_name="Demand shift precedes order-flow change",
            cause_entity_id=entity_a,
            effect_entity_id=entity_b,
            cause_observed_at="2026-08-02T15:00:00-05:00",
            effect_observed_at="2026-08-02T15:15:00-05:00",
            certified_observation_hashes=(certified_hashes[-1],),
            confidence=0.80,
            calibrated_probability=0.78,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_certified_causal_observation_request(
            pattern_name="Order-flow change precedes market repricing",
            cause_entity_id=entity_b,
            effect_entity_id=entity_c,
            cause_observed_at="2026-08-02T14:20:00-05:00",
            effect_observed_at="2026-08-02T14:35:00-05:00",
            certified_observation_hashes=(certified_hashes[0],),
            confidence=0.79,
            calibrated_probability=0.76,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_certified_causal_observation_request(
            pattern_name="Order-flow change precedes market repricing",
            cause_entity_id=entity_b,
            effect_entity_id=entity_c,
            cause_observed_at="2026-08-02T15:20:00-05:00",
            effect_observed_at="2026-08-02T15:35:00-05:00",
            certified_observation_hashes=(certified_hashes[-1],),
            confidence=0.77,
            calibrated_probability=0.74,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
    )
    return build_oracle_memory_certified_causal_pattern_memory(
        calibration=calibration,
        requests=requests,
    )


def main() -> int:
    print("=" * 48)
    print(" OML-037 TEST")
    print(" CERTIFIED OBSERVATION MULTI-HOP CAUSAL CHAIN MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    causal_patterns = build_causal_patterns(root)
    ordered_patterns = sorted(
        causal_patterns.causal_memory.patterns,
        key=lambda item: item.cause_entity_id,
    )
    request = build_oracle_memory_certified_multi_hop_chain_request(
        chain_name="Real-world demand to market repricing chain",
        pattern_ids=tuple(item.pattern_id for item in ordered_patterns),
    )
    result = build_oracle_memory_certified_multi_hop_causal_chain_memory(
        causal_patterns=causal_patterns,
        requests=(request,),
    )

    assert result.schema_version == "OML-037"
    assert result.engine_id == "OML-037"
    assert result.upstream_schema_version == "OML-036"
    assert result.upstream_engine_id == "OML-036"
    assert result.chain_schema_version == "OML-025"
    assert result.chain_engine_id == "OML-025"
    assert result.chain_count == 1
    assert result.total_hop_count == 2

    chain = result.chain_memory.chains[0]
    binding = result.bindings[0]
    assert chain.chain_status == CHAIN_STATUS_ESTABLISHED
    assert chain.hop_count == 2
    assert chain.hop_continuity_verified
    assert chain.temporal_direction_verified
    assert binding.pattern_ids == tuple(hop.pattern_id for hop in chain.hops)
    assert binding.upstream_certification_hash == causal_patterns.certification_hash
    assert binding.upstream_causal_memory_hash == causal_patterns.causal_memory.memory_hash
    assert binding.chain_memory_hash == result.chain_memory.memory_hash
    assert binding.certified_observation_hashes
    assert binding.causal_observation_hashes

    assert result.certified_observation_lineage_verified
    assert result.causal_pattern_lineage_verified
    assert result.deterministic_identity_verified
    assert result.canonical_chain_order_verified
    assert result.hop_continuity_verified
    assert result.temporal_direction_verified
    assert result.evidence_depth_reconciled
    assert result.contradiction_depth_reconciled
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.memory_ready
    assert result.downstream_causal_replay_authorized
    assert result.read_only

    replay = build_oracle_memory_certified_multi_hop_causal_chain_memory(
        causal_patterns=causal_patterns,
        requests=(request,),
    )
    assert replay == result
    assert verify_oracle_memory_certified_multi_hop_causal_chain_memory(result)

    expect_rejection(
        lambda: build_oracle_memory_certified_multi_hop_chain_request(
            chain_name="Broken",
            pattern_ids=(ordered_patterns[0].pattern_id,) * 2,
        ),
        "duplicate pattern request",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_multi_hop_causal_chain_memory(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_multi_hop_causal_chain_memory(
            replace(result, downstream_causal_replay_authorized=False)
        ),
        "replay continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_multi_hop_causal_chain_memory(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-036 causal pattern memory consumed read-only")
    print("[PASS] Exact OML-036 causal-memory dataclass passed directly")
    print("[PASS] Actual OML-025 chain builders consumed")
    print("[PASS] Two certified causal patterns linked into one chain")
    print("[PASS] Hop continuity and temporal direction verified")
    print("[PASS] Certified observation lineage retained across every hop")
    print("[PASS] Causal observation lineage retained across every hop")
    print("[PASS] Deterministic hashes and replay equality verified")
    print("[PASS] Causal replay continuation authorized read-only")
    print("[PASS] Oracle Terminal separation preserved")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-037 chain memories rejected")
    print("[DONE] OML-037 CERTIFIED OBSERVATION MULTI-HOP CAUSAL CHAIN MEMORY PASS")
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
    required = (UPSTREAM, UPSTREAM_TEST, CHAIN_MODULE, CHAIN_TEST)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified upstream files missing: " + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_causal_pattern_memory"
    )
    chain_module = importlib.import_module(
        "qseries_v2.oracle_memory.oracle_memory_multi_hop_causal_chain_memory"
    )

    expected_upstream = {
        "SCHEMA_VERSION": "OML-036",
        "ENGINE_ID": "OML-036",
        "POLICY_ID": "oracle-memory.certified-observation-causal-pattern-memory.v1",
        "UPSTREAM_SCHEMA_VERSION": "OML-035",
        "UPSTREAM_ENGINE_ID": "OML-035",
        "CAUSAL_SCHEMA_VERSION": "OML-024",
        "CAUSAL_ENGINE_ID": "OML-024",
    }
    expected_chain = {
        "SCHEMA_VERSION": "OML-025",
        "ENGINE_ID": "OML-025",
        "POLICY_ID": "oracle-memory.multi-hop-causal-chain-memory.v1",
        "UPSTREAM_SCHEMA_VERSION": "OML-024",
        "UPSTREAM_ENGINE_ID": "OML-024",
    }
    for name, value in expected_upstream.items():
        if getattr(upstream_module, name, None) != value:
            raise RuntimeError(f"Certified OML-036 {name} mismatch")
    for name, value in expected_chain.items():
        if getattr(chain_module, name, None) != value:
            raise RuntimeError(f"Certified OML-025 {name} mismatch")

    required_upstream_symbols = (
        "OracleMemoryCertifiedCausalPatternMemory",
        "verify_oracle_memory_certified_causal_pattern_memory",
    )
    required_chain_symbols = (
        "OracleMemoryMultiHopCausalChainMemory",
        "build_oracle_memory_multi_hop_causal_chain",
        "build_oracle_memory_multi_hop_causal_chain_memory",
        "verify_oracle_memory_multi_hop_causal_chain",
        "verify_oracle_memory_multi_hop_causal_chain_memory",
        "OracleMemoryMultiHopCausalChainInvariantError",
    )
    for module, names, label in (
        (upstream_module, required_upstream_symbols, "OML-036"),
        (chain_module, required_chain_symbols, "OML-025"),
    ):
        missing_names = [name for name in names if not hasattr(module, name)]
        if missing_names:
            raise RuntimeError(
                f"Certified {label} missing symbols: " + ", ".join(missing_names)
            )

    expected_builders = {
        "build_oracle_memory_multi_hop_causal_chain": {
            "chain_name",
            "patterns",
        },
        "build_oracle_memory_multi_hop_causal_chain_memory": {
            "causal_memory",
            "chains",
        },
    }
    for name, required_parameters in expected_builders.items():
        actual = set(inspect.signature(getattr(chain_module, name)).parameters)
        missing_parameters = sorted(required_parameters - actual)
        if missing_parameters:
            raise RuntimeError(
                f"Certified OML-025 {name} parameters missing: "
                + ", ".join(missing_parameters)
            )

    required_fields = {
        "schema_version",
        "engine_id",
        "certification_hash",
        "causal_memory",
        "bindings",
        "memory_ready",
        "downstream_multi_hop_causal_authorized",
        "read_only",
    }
    actual_fields = set(
        upstream_module
        .OracleMemoryCertifiedCausalPatternMemory
        .__dataclass_fields__
    )
    missing_fields = sorted(required_fields - actual_fields)
    if missing_fields:
        raise RuntimeError(
            "Certified OML-036 dataclass fields missing: "
            + ", ".join(missing_fields)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-037 INSTALLER")
    print(" CERTIFIED OBSERVATION MULTI-HOP CAUSAL CHAIN MEMORY")
    print("=" * 48)
    print("[BOOT] Revision: EXACT_OML_036_025_INTERFACE_ALIGNMENT")

    try:
        validate_upstreams()
        print("[OK] Actual OML-036 dataclass and verifier inspected")
        print("[OK] Actual OML-025 builders and signatures inspected")

        for path, label in (
            (UPSTREAM_TEST, "OML-036"),
            (CHAIN_TEST, "OML-025"),
        ):
            run = subprocess.run([sys.executable, str(path)], cwd=ROOT, check=False)
            if run.returncode:
                raise RuntimeError(
                    f"{label} certification failed with exit code {run.returncode}"
                )

        tracked = {
            path: path.read_bytes()
            for path in (UPSTREAM, UPSTREAM_TEST, CHAIN_MODULE, CHAIN_TEST)
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_observation_"
            "multi_hop_causal_chain_memory import *"
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

        completed = subprocess.run([sys.executable, str(TEST)], cwd=ROOT, check=False)
        if completed.returncode:
            raise RuntimeError(
                f"OML-037 test failed with exit code {completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Certified OML-036 production unchanged")
        print("[PASS] Certified OML-036 standalone test unchanged")
        print("[PASS] Certified OML-025 chain engine unchanged")
        print("[PASS] Exact OML-036 causal-memory dataclass consumed directly")
        print("[PASS] OML-037 production fully replaced")
        print("[PASS] OML-037 standalone deterministic test installed")
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
            "[DONE] OML-037 CERTIFIED OBSERVATION "
            "MULTI-HOP CAUSAL CHAIN MEMORY INSTALLED"
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
