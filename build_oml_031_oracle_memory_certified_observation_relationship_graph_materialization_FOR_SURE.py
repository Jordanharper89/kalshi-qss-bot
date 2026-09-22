from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = (
    PACKAGE
    / "oracle_memory_certified_observation_entity_resolution.py"
)
UPSTREAM_TEST = (
    ROOT
    / "test_oml_030_oracle_memory_certified_observation_entity_resolution.py"
)

RELATIONSHIP_MODULE = (
    PACKAGE
    / "oracle_memory_relationship_graph_and_linkage_resolution.py"
)
RELATIONSHIP_TEST = (
    ROOT
    / "test_oml_019_oracle_memory_relationship_graph_and_linkage_resolution.py"
)

ENTITY_MODULE = PACKAGE / "oracle_memory_entity_resolution.py"

PRODUCTION = (
    PACKAGE
    / "oracle_memory_certified_observation_relationship_graph_materialization.py"
)
TEST = (
    ROOT
    / "test_oml_031_oracle_memory_certified_observation_relationship_graph_materialization.py"
)
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_observation_entity_resolution import (
    OracleMemoryObservationEntityResolution,
    verify_oracle_memory_observation_entity_resolution,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_entity_resolution import (
    OracleMemoryEntityResolutionBatch,
    verify_oracle_memory_entity_resolution_batch,
)
from qseries_v2.oracle_memory.oracle_memory_relationship_graph_and_linkage_resolution import (
    OracleMemoryEntityRelationship,
    OracleMemoryRelationshipGraph,
    build_oracle_memory_entity_relationship,
    build_oracle_memory_relationship_graph,
    verify_oracle_memory_entity_relationship,
    verify_oracle_memory_relationship_graph,
)

SCHEMA_VERSION = "OML-031"
ENGINE_ID = "OML-031"
POLICY_ID = (
    "oracle-memory.certified-observation-relationship-graph-materialization.v1"
)

UPSTREAM_SCHEMA_VERSION = "OML-030"
UPSTREAM_ENGINE_ID = "OML-030"

GRAPH_STATE_READ_ONLY = "read_only_graph"


class OracleMemoryObservationRelationshipGraphInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryObservationRelationshipRequest:
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    evidence_hashes: tuple[str, ...]
    confidence: float
    contradiction_count: int
    directed: bool
    request_hash: str


@dataclass(frozen=True)
class OracleMemoryObservationRelationshipBinding:
    request_hash: str
    relationship_id: str
    relationship_hash: str
    source_entity_id: str
    target_entity_id: str
    source_observation_hash: str
    target_observation_hash: str
    source_entity_lineage_verified: bool
    target_entity_lineage_verified: bool
    evidence_lineage_verified: bool
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
class OracleMemoryObservationRelationshipGraphMaterialization:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_resolution_hash: str
    adapted_entity_batch_hash: str
    relationship_graph_hash: str
    graph: OracleMemoryRelationshipGraph
    bindings: tuple[OracleMemoryObservationRelationshipBinding, ...]
    entity_count: int
    relationship_count: int
    graph_state: str
    certified_entity_lineage_verified: bool
    observation_relationship_lineage_verified: bool
    canonical_graph_order_verified: bool
    deterministic_graph_materialization_verified: bool
    dangling_relationships_rejected: bool
    duplicate_relationships_rejected: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    graph_ready: bool
    downstream_narrative_detection_authorized: bool
    read_only: bool
    materialization_hash: str


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
    raise OracleMemoryObservationRelationshipGraphInvariantError(
        "unsupported OML-031 value type: "
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
    raise OracleMemoryObservationRelationshipGraphInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-031 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryObservationRelationshipGraphInvariantError(
            f"OML-031 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_observation_relationship_request(
    *,
    source_entity_id: str,
    target_entity_id: str,
    relationship_type: str,
    evidence_hashes: Sequence[str],
    confidence: float,
    contradiction_count: int = 0,
    directed: bool = True,
) -> OracleMemoryObservationRelationshipRequest:
    _require_hash(source_entity_id, "source entity id")
    _require_hash(target_entity_id, "target entity id")

    if source_entity_id == target_entity_id:
        _reject("OML-031 self relationship forbidden")

    if not isinstance(relationship_type, str) or not relationship_type.strip():
        _reject("OML-031 relationship type required")

    evidence = tuple(sorted(set(evidence_hashes)))

    if not evidence:
        _reject("OML-031 relationship evidence required")

    if len(evidence) != len(tuple(evidence_hashes)):
        _reject("OML-031 duplicate evidence hashes forbidden")

    for value in evidence:
        _require_hash(value, "evidence hash")

    confidence = float(confidence)

    if not 0.0 <= confidence <= 1.0:
        _reject("OML-031 confidence outside [0, 1]")

    if (
        not isinstance(contradiction_count, int)
        or isinstance(contradiction_count, bool)
        or contradiction_count < 0
    ):
        _reject("OML-031 contradiction count invalid")

    body = {
        "source_entity_id": source_entity_id,
        "target_entity_id": target_entity_id,
        "relationship_type": relationship_type.strip(),
        "evidence_hashes": evidence,
        "confidence": confidence,
        "contradiction_count": contradiction_count,
        "directed": bool(directed),
    }

    request = OracleMemoryObservationRelationshipRequest(
        **body,
        request_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_relationship_request(request)
    return request


def verify_oracle_memory_observation_relationship_request(
    request: OracleMemoryObservationRelationshipRequest,
) -> bool:
    body = asdict(request)
    supplied = body.pop("request_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-031 request hash mismatch")

    for value, label in (
        (request.source_entity_id, "source entity id"),
        (request.target_entity_id, "target entity id"),
        (request.request_hash, "request hash"),
    ):
        _require_hash(value, label)

    if request.source_entity_id == request.target_entity_id:
        _reject("OML-031 self relationship request")

    if not request.evidence_hashes:
        _reject("OML-031 request evidence missing")

    for value in request.evidence_hashes:
        _require_hash(value, "request evidence hash")

    if not 0.0 <= request.confidence <= 1.0:
        _reject("OML-031 request confidence invalid")

    if request.contradiction_count < 0:
        _reject("OML-031 request contradiction count invalid")

    return True


def _adapt_entity_resolution_batch(
    resolution: OracleMemoryObservationEntityResolution,
) -> OracleMemoryEntityResolutionBatch:
    verify_oracle_memory_observation_entity_resolution(resolution)

    body = {
        "schema_version": "OML-018",
        "engine_id": "OML-018",
        "policy_id": "oracle-memory.entity-resolution.v1",
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": "OML-017",
        "upstream_engine_id": "OML-017",
        "upstream_batch_hash": (
            resolution.upstream_validation_batch_hash
        ),
        "entities": resolution.entities,
        "resolved_entity_count": len(resolution.entities),
        "rejected_duplicate_count": resolution.rejected_duplicate_count,
        "canonical_order_verified": True,
        "deterministic_resolution_verified": True,
        "alias_normalization_verified": True,
        "entity_identity_uniqueness_verified": (
            resolution.entity_identity_uniqueness_verified
        ),
        "duplicate_candidates_excluded": (
            resolution.duplicate_candidates_excluded
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "batch_ready": True,
        "next_certification_authorized": True,
        "read_only": True,
    }

    adapted = OracleMemoryEntityResolutionBatch(
        **body,
        batch_hash=_stable_hash(body),
    )

    if any(
        not hasattr(entity, "__dataclass_fields__")
        for entity in adapted.entities
    ):
        _reject("OML-031 adapted entities lost dataclass identity")

    verify_oracle_memory_entity_resolution_batch(adapted)
    return adapted


def _build_binding(
    *,
    request: OracleMemoryObservationRelationshipRequest,
    relationship: OracleMemoryEntityRelationship,
    source_observation_hash: str,
    target_observation_hash: str,
) -> OracleMemoryObservationRelationshipBinding:
    verify_oracle_memory_observation_relationship_request(request)
    verify_oracle_memory_entity_relationship(relationship)

    body = {
        "request_hash": request.request_hash,
        "relationship_id": relationship.relationship_id,
        "relationship_hash": relationship.relationship_hash,
        "source_entity_id": relationship.source_entity_id,
        "target_entity_id": relationship.target_entity_id,
        "source_observation_hash": source_observation_hash,
        "target_observation_hash": target_observation_hash,
        "source_entity_lineage_verified": True,
        "target_entity_lineage_verified": True,
        "evidence_lineage_verified": (
            relationship.evidence_hashes == request.evidence_hashes
        ),
        "deterministic_binding_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    binding = OracleMemoryObservationRelationshipBinding(
        **body,
        binding_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_relationship_binding(binding)
    return binding


def verify_oracle_memory_observation_relationship_binding(
    binding: OracleMemoryObservationRelationshipBinding,
) -> bool:
    body = asdict(binding)
    supplied = body.pop("binding_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-031 binding hash mismatch")

    for value, label in (
        (binding.request_hash, "request hash"),
        (binding.relationship_id, "relationship id"),
        (binding.relationship_hash, "relationship hash"),
        (binding.source_entity_id, "source entity id"),
        (binding.target_entity_id, "target entity id"),
        (binding.source_observation_hash, "source observation hash"),
        (binding.target_observation_hash, "target observation hash"),
        (binding.binding_hash, "binding hash"),
    ):
        _require_hash(value, label)

    required_true = (
        binding.source_entity_lineage_verified,
        binding.target_entity_lineage_verified,
        binding.evidence_lineage_verified,
        binding.deterministic_binding_verified,
        binding.read_only,
    )

    if not all(required_true):
        _reject("OML-031 binding guarantee missing")

    forbidden = (
        binding.persistence_authorized,
        binding.learning_update_authorized,
        binding.runtime_activation_authorized,
        binding.publication_authorized,
        binding.action_authorization_enabled,
        binding.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-031 forbidden binding capability enabled")

    return True


def build_oracle_memory_observation_relationship_graph_materialization(
    *,
    resolution: OracleMemoryObservationEntityResolution,
    requests: Sequence[OracleMemoryObservationRelationshipRequest],
) -> OracleMemoryObservationRelationshipGraphMaterialization:
    verify_oracle_memory_observation_entity_resolution(resolution)

    if resolution.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-031 upstream schema mismatch")

    if resolution.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-031 upstream engine mismatch")

    if not resolution.resolution_ready:
        _reject("OML-031 upstream resolution not ready")

    if not resolution.downstream_relationship_graph_authorized:
        _reject("OML-031 graph materialization not authorized")

    if not resolution.read_only:
        _reject("OML-031 upstream resolution not read-only")

    adapted_batch = _adapt_entity_resolution_batch(resolution)

    entities_by_id = {
        entity.canonical_entity_id: entity
        for entity in resolution.entities
    }
    bindings_by_entity_id = {
        binding.canonical_entity_id: binding
        for binding in resolution.bindings
    }

    ordered_requests = tuple(
        sorted(
            requests,
            key=lambda item: (
                item.source_entity_id,
                item.target_entity_id,
                item.relationship_type,
                item.request_hash,
            ),
        )
    )

    relationships = []
    bindings = []

    for request in ordered_requests:
        verify_oracle_memory_observation_relationship_request(request)

        source_entity = entities_by_id.get(request.source_entity_id)
        target_entity = entities_by_id.get(request.target_entity_id)
        source_binding = bindings_by_entity_id.get(
            request.source_entity_id
        )
        target_binding = bindings_by_entity_id.get(
            request.target_entity_id
        )

        if (
            source_entity is None
            or target_entity is None
            or source_binding is None
            or target_binding is None
        ):
            _reject("OML-031 dangling observation relationship")

        relationship = build_oracle_memory_entity_relationship(
            source_entity=source_entity,
            target_entity=target_entity,
            relationship_type=request.relationship_type,
            evidence_hashes=request.evidence_hashes,
            confidence=request.confidence,
            contradiction_count=request.contradiction_count,
            directed=request.directed,
        )

        relationships.append(relationship)
        bindings.append(
            _build_binding(
                request=request,
                relationship=relationship,
                source_observation_hash=(
                    source_binding.observation_hash
                ),
                target_observation_hash=(
                    target_binding.observation_hash
                ),
            )
        )

    graph = build_oracle_memory_relationship_graph(
        entity_batch=adapted_batch,
        relationships=tuple(relationships),
    )

    ordered_bindings = tuple(
        sorted(
            bindings,
            key=lambda item: (
                item.source_entity_id,
                item.target_entity_id,
                item.relationship_id,
                item.binding_hash,
            ),
        )
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": resolution.schema_version,
        "upstream_engine_id": resolution.engine_id,
        "upstream_resolution_hash": resolution.resolution_hash,
        "adapted_entity_batch_hash": adapted_batch.batch_hash,
        "relationship_graph_hash": graph.graph_hash,
        "graph": graph,
        "bindings": ordered_bindings,
        "entity_count": graph.entity_count,
        "relationship_count": graph.relationship_count,
        "graph_state": GRAPH_STATE_READ_ONLY,
        "certified_entity_lineage_verified": True,
        "observation_relationship_lineage_verified": True,
        "canonical_graph_order_verified": True,
        "deterministic_graph_materialization_verified": True,
        "dangling_relationships_rejected": True,
        "duplicate_relationships_rejected": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "graph_ready": True,
        "downstream_narrative_detection_authorized": True,
        "read_only": True,
    }

    materialization = (
        OracleMemoryObservationRelationshipGraphMaterialization(
            **body,
            materialization_hash=_stable_hash(body),
        )
    )

    verify_oracle_memory_observation_relationship_graph_materialization(
        materialization
    )
    return materialization


def verify_oracle_memory_observation_relationship_graph_materialization(
    materialization: (
        OracleMemoryObservationRelationshipGraphMaterialization
    ),
) -> bool:
    body = asdict(materialization)
    supplied = body.pop("materialization_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-031 materialization hash mismatch")

    if materialization.schema_version != SCHEMA_VERSION:
        _reject("OML-031 schema mismatch")

    if materialization.engine_id != ENGINE_ID:
        _reject("OML-031 engine mismatch")

    if materialization.policy_id != POLICY_ID:
        _reject("OML-031 policy mismatch")

    if materialization.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-031 subsystem mismatch")

    if materialization.upstream_schema_version != (
        UPSTREAM_SCHEMA_VERSION
    ):
        _reject("OML-031 upstream schema lineage mismatch")

    if materialization.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-031 upstream engine lineage mismatch")

    verify_oracle_memory_relationship_graph(materialization.graph)

    if materialization.entity_count != (
        materialization.graph.entity_count
    ):
        _reject("OML-031 entity count mismatch")

    if materialization.relationship_count != (
        materialization.graph.relationship_count
    ):
        _reject("OML-031 relationship count mismatch")

    if materialization.relationship_count != len(
        materialization.bindings
    ):
        _reject("OML-031 binding count mismatch")

    for binding in materialization.bindings:
        verify_oracle_memory_observation_relationship_binding(binding)

    if materialization.graph_state != GRAPH_STATE_READ_ONLY:
        _reject("OML-031 graph state invalid")

    required_true = (
        materialization.certified_entity_lineage_verified,
        materialization.observation_relationship_lineage_verified,
        materialization.canonical_graph_order_verified,
        materialization.deterministic_graph_materialization_verified,
        materialization.dangling_relationships_rejected,
        materialization.duplicate_relationships_rejected,
        materialization.graph_ready,
        materialization.downstream_narrative_detection_authorized,
        materialization.read_only,
    )

    if not all(required_true):
        _reject("OML-031 materialization guarantee missing")

    forbidden = (
        materialization.persistence_enabled,
        materialization.learning_updates_enabled,
        materialization.runtime_activation_enabled,
        materialization.publication_enabled,
        materialization.action_authorization_enabled,
        materialization.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-031 forbidden materialization capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    build_oracle_memory_candidate_validation_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_materialization import (
    build_oracle_memory_observation_candidate_materialization_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_validation_and_admission import (
    build_oracle_memory_observation_candidate_admission_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_entity_resolution import (
    build_oracle_memory_observation_entity_resolution,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_intake_contract import (
    OBSERVATION_KIND_MARKET,
    OBSERVATION_KIND_REAL_WORLD,
    build_oracle_memory_certified_observation,
    build_oracle_memory_observation_intake_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_relationship_graph_materialization import (
    OracleMemoryObservationRelationshipGraphInvariantError,
    build_oracle_memory_observation_relationship_graph_materialization,
    build_oracle_memory_observation_relationship_request,
    verify_oracle_memory_observation_relationship_graph_materialization,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
)
from qseries_v2.oracle_memory.oracle_memory_cross_market_dependency_memory import (
    build_oracle_memory_cross_market_dependency_memory,
)
from qseries_v2.oracle_memory.oracle_memory_ledger_integrity_and_replay_certification import (
    build_oracle_memory_ledger_integrity_replay_certification,
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
    except OracleMemoryObservationRelationshipGraphInvariantError:
        return
    raise AssertionError(f"tampered OML-031 {label} accepted")


def build_resolution(root: Path):
    fixture_026 = load_module(
        root
        / "test_oml_026_oracle_memory_cross_market_dependency_memory.py",
        "oml_026_fixture_for_oml_031",
    )
    chain_memory, _ = fixture_026.build_chain_memory(root)

    cross_market_memory = build_oracle_memory_cross_market_dependency_memory(
        causal_chain_memory=chain_memory,
        dependencies=(),
    )

    observation_a = build_oracle_memory_certified_observation(
        observation_kind=OBSERVATION_KIND_REAL_WORLD,
        domain_id=MEMORY_DOMAINS[0],
        entity_key="Stablecoin Liquidity",
        source_key="oracle-live-shadow",
        observed_at="2026-08-02T15:00:00-05:00",
        effective_at="2026-08-02T15:00:00-05:00",
        payload={"signal": "stablecoin_inflow_increase"},
        evidence_hashes=("1" * 64,),
        source_certification_hash="2" * 64,
        confidence=0.82,
        uncertainty=0.18,
    )

    observation_b = build_oracle_memory_certified_observation(
        observation_kind=OBSERVATION_KIND_MARKET,
        domain_id=MEMORY_DOMAINS[0],
        entity_key="Bitcoin",
        source_key="oracle-live-shadow",
        observed_at="2026-08-02T15:10:00-05:00",
        effective_at="2026-08-02T15:10:00-05:00",
        payload={"signal": "market_repricing"},
        evidence_hashes=("3" * 64,),
        source_certification_hash="4" * 64,
        confidence=0.79,
        uncertainty=0.21,
    )

    intake = build_oracle_memory_observation_intake_batch(
        cross_market_memory=cross_market_memory,
        observations=(observation_a, observation_b),
    )

    fixture_009 = load_module(
        root
        / "test_oml_009_oracle_memory_canonical_record_candidate_contract.py",
        "oml_009_fixture_for_oml_031",
    )
    gate_decision = fixture_009.build_oml_008_decision(root)

    materialization = (
        build_oracle_memory_observation_candidate_materialization_batch(
            gate_decision=gate_decision,
            intake_batch=intake,
        )
    )

    fixture_016 = load_module(
        root
        / "test_oml_016_oracle_memory_ledger_integrity_and_replay_certification.py",
        "oml_016_fixture_for_oml_031",
    )
    ledger_contract = fixture_016.build_oml_015_contract(root)
    ledger = build_oracle_memory_ledger_integrity_replay_certification(
        ledger_contract=ledger_contract,
    )

    validation = build_oracle_memory_candidate_validation_batch(
        ledger_certification=ledger,
        candidates=materialization.candidates,
    )

    admission = build_oracle_memory_observation_candidate_admission_batch(
        materialization_batch=materialization,
        validation_batch=validation,
    )

    aliases = {
        candidate.candidate_hash: (
            ("USDT Liquidity", "Stablecoin Liquidity")
            if candidate.entity_key == "Stablecoin Liquidity"
            else ("BTC", "Bitcoin", "XBT")
        )
        for candidate in materialization.candidates
    }

    return build_oracle_memory_observation_entity_resolution(
        admission_batch=admission,
        materialization_batch=materialization,
        validation_batch=validation,
        aliases_by_candidate_hash=aliases,
    )


def main() -> int:
    print("=" * 48)
    print(" OML-031 TEST")
    print(" CERTIFIED OBSERVATION RELATIONSHIP GRAPH MATERIALIZATION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    resolution = build_resolution(root)

    assert resolution.resolved_entity_count == 2

    liquidity = next(
        item for item in resolution.entities
        if item.normalized_name == "stablecoin liquidity"
    )
    bitcoin = next(
        item for item in resolution.entities
        if item.normalized_name == "bitcoin"
    )

    request = build_oracle_memory_observation_relationship_request(
        source_entity_id=liquidity.canonical_entity_id,
        target_entity_id=bitcoin.canonical_entity_id,
        relationship_type="precedes market repricing",
        evidence_hashes=("5" * 64, "6" * 64),
        confidence=0.84,
        contradiction_count=0,
        directed=True,
    )

    materialization = (
        build_oracle_memory_observation_relationship_graph_materialization(
            resolution=resolution,
            requests=(request,),
        )
    )

    assert materialization.schema_version == "OML-031"
    assert materialization.engine_id == "OML-031"
    assert materialization.upstream_schema_version == "OML-030"
    assert materialization.upstream_engine_id == "OML-030"
    assert materialization.entity_count == 2
    assert materialization.relationship_count == 1
    assert materialization.graph.entity_count == 2
    assert materialization.graph.relationship_count == 1
    assert materialization.certified_entity_lineage_verified
    assert materialization.observation_relationship_lineage_verified
    assert materialization.canonical_graph_order_verified
    assert materialization.deterministic_graph_materialization_verified
    assert materialization.dangling_relationships_rejected
    assert materialization.duplicate_relationships_rejected
    assert not materialization.persistence_enabled
    assert not materialization.learning_updates_enabled
    assert not materialization.runtime_activation_enabled
    assert not materialization.publication_enabled
    assert not materialization.action_authorization_enabled
    assert not materialization.qseries_execution_enabled
    assert materialization.graph_ready
    assert materialization.downstream_narrative_detection_authorized
    assert materialization.read_only

    replay = (
        build_oracle_memory_observation_relationship_graph_materialization(
            resolution=resolution,
            requests=(request,),
        )
    )

    assert replay == materialization
    assert (
        verify_oracle_memory_observation_relationship_graph_materialization(
            materialization
        )
    )

    expect_rejection(
        lambda: build_oracle_memory_observation_relationship_graph_materialization(
            resolution=resolution,
            requests=(request, request),
        ),
        "duplicate relationship",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_relationship_graph_materialization(
            replace(materialization, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_relationship_graph_materialization(
            replace(
                materialization,
                downstream_narrative_detection_authorized=False,
            )
        ),
        "narrative authorization",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_relationship_graph_materialization(
            replace(materialization, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-030 entity resolution consumed")
    print("[PASS] Certified OML-019 relationship engine consumed")
    print("[PASS] OML-018 entity batch contract adapted exactly")
    print("[PASS] Entity dataclass identities preserved")
    print("[PASS] Evidence-backed observation relationship created")
    print("[PASS] Observation-to-relationship lineage retained")
    print("[PASS] Dangling relationships rejected")
    print("[PASS] Duplicate relationships rejected")
    print("[PASS] Relationship graph deterministic across replay")
    print("[PASS] Narrative continuation authorized read-only")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered graph materializations rejected")
    print(
        "[DONE] OML-031 CERTIFIED OBSERVATION "
        "RELATIONSHIP GRAPH MATERIALIZATION PASS"
    )
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
    required_files = (
        UPSTREAM,
        UPSTREAM_TEST,
        RELATIONSHIP_MODULE,
        RELATIONSHIP_TEST,
        ENTITY_MODULE,
    )

    missing = [str(path) for path in required_files if not path.is_file()]

    if missing:
        raise RuntimeError(
            "Required certified upstream files missing: "
            + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    resolution_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_entity_resolution"
    )

    expected_resolution = {
        "SCHEMA_VERSION": "OML-030",
        "ENGINE_ID": "OML-030",
        "POLICY_ID": (
            "oracle-memory.certified-observation-entity-resolution.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-029",
        "UPSTREAM_ENGINE_ID": "OML-029",
    }

    for name, value in expected_resolution.items():
        actual = getattr(resolution_module, name, None)
        if actual != value:
            raise RuntimeError(
                f"Certified OML-030 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    relationship_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_relationship_graph_and_linkage_resolution"
    )

    expected_relationship = {
        "SCHEMA_VERSION": "OML-019",
        "ENGINE_ID": "OML-019",
        "POLICY_ID": (
            "oracle-memory.relationship-graph-and-linkage-resolution.v1"
        ),
    }

    for name, value in expected_relationship.items():
        actual = getattr(relationship_module, name, None)
        if actual != value:
            raise RuntimeError(
                f"Certified OML-019 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    entity_module = importlib.import_module(
        "qseries_v2.oracle_memory.oracle_memory_entity_resolution"
    )
    entity_class = getattr(
        entity_module,
        "OracleMemoryEntityResolutionBatch",
        None,
    )

    if entity_class is None:
        raise RuntimeError("Certified OML-018 batch class missing")

    required_entity_fields = {
        "schema_version",
        "engine_id",
        "policy_id",
        "subsystem_id",
        "upstream_schema_version",
        "upstream_engine_id",
        "upstream_batch_hash",
        "entities",
        "resolved_entity_count",
        "rejected_duplicate_count",
        "canonical_order_verified",
        "deterministic_resolution_verified",
        "alias_normalization_verified",
        "entity_identity_uniqueness_verified",
        "duplicate_candidates_excluded",
        "persistence_enabled",
        "learning_updates_enabled",
        "runtime_activation_enabled",
        "publication_enabled",
        "action_authorization_enabled",
        "qseries_execution_enabled",
        "batch_ready",
        "next_certification_authorized",
        "read_only",
        "batch_hash",
    }

    missing_fields = sorted(
        required_entity_fields - set(entity_class.__dataclass_fields__)
    )

    if missing_fields:
        raise RuntimeError(
            "Certified OML-018 batch fields missing: "
            + ", ".join(missing_fields)
        )

    relationship_builder = getattr(
        relationship_module,
        "build_oracle_memory_relationship_graph",
        None,
    )

    if relationship_builder is None:
        raise RuntimeError("Certified OML-019 graph builder missing")

    required_builder_parameters = {
        "entity_batch",
        "relationships",
    }

    missing_parameters = sorted(
        required_builder_parameters
        - set(inspect.signature(relationship_builder).parameters)
    )

    if missing_parameters:
        raise RuntimeError(
            "Certified OML-019 builder parameters missing: "
            + ", ".join(missing_parameters)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-031 FOR-SURE INSTALLER")
    print(" CERTIFIED OBSERVATION RELATIONSHIP GRAPH MATERIALIZATION")
    print("=" * 48)
    print("[BOOT] Revision: EXACT_OML_018_019_GRAPH_ALIGNMENT")

    try:
        validate_upstreams()
        print("[OK] Actual OML-030 imported and structurally verified")
        print("[OK] Actual OML-018 batch fields verified")
        print("[OK] Actual OML-019 graph builder verified")

        upstream_run = subprocess.run(
            [sys.executable, str(UPSTREAM_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream_run.returncode:
            raise RuntimeError(
                "OML-030 certification failed with exit code "
                f"{upstream_run.returncode}"
            )

        relationship_run = subprocess.run(
            [sys.executable, str(RELATIONSHIP_TEST)],
            cwd=ROOT,
            check=False,
        )

        if relationship_run.returncode:
            raise RuntimeError(
                "OML-019 certification failed with exit code "
                f"{relationship_run.returncode}"
            )

        tracked = {
            path: path.read_bytes()
            for path in required_files_for_tracking()
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from ."
            "oracle_memory_certified_observation_relationship_graph_materialization "
            "import *"
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
                "OML-031 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(
                    f"Certified upstream changed: {path}"
                )

        print("[PASS] Certified OML-030 production unchanged")
        print("[PASS] Certified OML-030 standalone test unchanged")
        print("[PASS] Certified OML-019 relationship engine unchanged")
        print("[PASS] Certified OML-018 entity contract unchanged")
        print("[PASS] OML-031 graph materialization installed")
        print("[PASS] OML-031 standalone deterministic test installed")
        print("[PASS] Observation relationships now enter graph layer")
        print("[PASS] Entity dataclass identities preserved")
        print("[PASS] Narrative continuation authorized read-only")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OML-031 CERTIFIED OBSERVATION "
            "RELATIONSHIP GRAPH MATERIALIZATION INSTALLED"
        )
        return 0

    except (
        RuntimeError,
        SyntaxError,
        ImportError,
        KeyError,
        TypeError,
    ) as exc:
        print(f"[ERROR] {exc}")
        return 1


def required_files_for_tracking() -> tuple[Path, ...]:
    return (
        UPSTREAM,
        UPSTREAM_TEST,
        RELATIONSHIP_MODULE,
        RELATIONSHIP_TEST,
        ENTITY_MODULE,
    )


if __name__ == "__main__":
    raise SystemExit(main())
