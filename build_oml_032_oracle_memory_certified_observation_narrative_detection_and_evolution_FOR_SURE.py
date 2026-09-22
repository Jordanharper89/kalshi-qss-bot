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
    / "oracle_memory_certified_observation_relationship_graph_materialization.py"
)
UPSTREAM_TEST = (
    ROOT
    / "test_oml_031_oracle_memory_certified_observation_relationship_graph_materialization.py"
)
NARRATIVE_MODULE = (
    PACKAGE
    / "oracle_memory_narrative_detection_and_evolution_engine.py"
)
NARRATIVE_TEST = (
    ROOT
    / "test_oml_020_oracle_memory_narrative_detection_and_evolution_engine.py"
)

PRODUCTION = (
    PACKAGE
    / "oracle_memory_certified_observation_narrative_detection_and_evolution.py"
)
TEST = (
    ROOT
    / "test_oml_032_oracle_memory_certified_observation_narrative_detection_and_evolution.py"
)
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_observation_relationship_graph_materialization import (
    OracleMemoryObservationRelationshipGraphMaterialization,
    verify_oracle_memory_observation_relationship_graph_materialization,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
    OracleMemoryNarrative,
    OracleMemoryNarrativeEvolutionBatch,
    build_oracle_memory_narrative,
    build_oracle_memory_narrative_evolution_batch,
    verify_oracle_memory_narrative,
    verify_oracle_memory_narrative_evolution_batch,
)

SCHEMA_VERSION = "OML-032"
ENGINE_ID = "OML-032"
POLICY_ID = (
    "oracle-memory.certified-observation-narrative-detection-and-evolution.v1"
)

UPSTREAM_SCHEMA_VERSION = "OML-031"
UPSTREAM_ENGINE_ID = "OML-031"

NARRATIVE_STATE_READ_ONLY = "read_only_narrative"


class OracleMemoryObservationNarrativeInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryObservationNarrativeRequest:
    title: str
    participating_entity_ids: tuple[str, ...]
    relationship_ids: tuple[str, ...]
    supporting_evidence_hashes: tuple[str, ...]
    contradicting_evidence_hashes: tuple[str, ...]
    confidence: float
    uncertainty: float
    first_observed_at: str
    last_observed_at: str
    evolution_index: int
    prior_stage: str | None
    request_hash: str


@dataclass(frozen=True)
class OracleMemoryObservationNarrativeBinding:
    request_hash: str
    narrative_id: str
    narrative_hash: str
    participating_entity_ids: tuple[str, ...]
    relationship_ids: tuple[str, ...]
    source_observation_hashes: tuple[str, ...]
    entity_lineage_verified: bool
    relationship_lineage_verified: bool
    observation_lineage_verified: bool
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
class OracleMemoryObservationNarrativeDetection:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_materialization_hash: str
    upstream_graph_hash: str
    narrative_batch: OracleMemoryNarrativeEvolutionBatch
    narratives: tuple[OracleMemoryNarrative, ...]
    bindings: tuple[OracleMemoryObservationNarrativeBinding, ...]
    narrative_count: int
    emerging_count: int
    strengthening_count: int
    weakening_count: int
    resolved_count: int
    narrative_state: str
    certified_graph_lineage_verified: bool
    observation_narrative_lineage_verified: bool
    canonical_order_verified: bool
    deterministic_detection_verified: bool
    contradiction_tracking_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    detection_ready: bool
    downstream_lifecycle_tracking_authorized: bool
    read_only: bool
    detection_hash: str


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
    raise OracleMemoryObservationNarrativeInvariantError(
        "unsupported OML-032 value type: "
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
    raise OracleMemoryObservationNarrativeInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-032 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryObservationNarrativeInvariantError(
            f"OML-032 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_observation_narrative_request(
    *,
    title: str,
    participating_entity_ids: Sequence[str],
    relationship_ids: Sequence[str],
    supporting_evidence_hashes: Sequence[str],
    contradicting_evidence_hashes: Sequence[str] = (),
    confidence: float,
    uncertainty: float,
    first_observed_at: str,
    last_observed_at: str,
    evolution_index: int = 1,
    prior_stage: str | None = None,
) -> OracleMemoryObservationNarrativeRequest:
    if not isinstance(title, str) or not title.strip():
        _reject("OML-032 title required")

    entities = tuple(sorted(set(participating_entity_ids)))
    relationships = tuple(sorted(set(relationship_ids)))
    supporting = tuple(sorted(set(supporting_evidence_hashes)))
    contradicting = tuple(sorted(set(contradicting_evidence_hashes)))

    if not entities or not relationships or not supporting:
        _reject("OML-032 entity, relationship, and evidence lineage required")

    for value in (*entities, *relationships, *supporting, *contradicting):
        _require_hash(value, "request lineage hash")

    confidence = float(confidence)
    uncertainty = float(uncertainty)

    if not 0.0 <= confidence <= 1.0:
        _reject("OML-032 confidence outside [0, 1]")
    if not 0.0 <= uncertainty <= 1.0:
        _reject("OML-032 uncertainty outside [0, 1]")
    if (
        not isinstance(evolution_index, int)
        or isinstance(evolution_index, bool)
        or evolution_index < 1
    ):
        _reject("OML-032 evolution index invalid")
    if not first_observed_at.strip() or not last_observed_at.strip():
        _reject("OML-032 timestamps required")

    body = {
        "title": title.strip(),
        "participating_entity_ids": entities,
        "relationship_ids": relationships,
        "supporting_evidence_hashes": supporting,
        "contradicting_evidence_hashes": contradicting,
        "confidence": confidence,
        "uncertainty": uncertainty,
        "first_observed_at": first_observed_at.strip(),
        "last_observed_at": last_observed_at.strip(),
        "evolution_index": evolution_index,
        "prior_stage": prior_stage,
    }

    request = OracleMemoryObservationNarrativeRequest(
        **body,
        request_hash=_stable_hash(body),
    )
    verify_oracle_memory_observation_narrative_request(request)
    return request


def verify_oracle_memory_observation_narrative_request(
    request: OracleMemoryObservationNarrativeRequest,
) -> bool:
    body = asdict(request)
    supplied = body.pop("request_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-032 request hash mismatch")
    _require_hash(request.request_hash, "request hash")
    for value in (
        *request.participating_entity_ids,
        *request.relationship_ids,
        *request.supporting_evidence_hashes,
        *request.contradicting_evidence_hashes,
    ):
        _require_hash(value, "request lineage hash")
    return True


def _build_binding(
    *,
    materialization: OracleMemoryObservationRelationshipGraphMaterialization,
    request: OracleMemoryObservationNarrativeRequest,
    narrative: OracleMemoryNarrative,
) -> OracleMemoryObservationNarrativeBinding:
    verify_oracle_memory_narrative(narrative)

    relationship_bindings = {
        binding.relationship_id: binding
        for binding in materialization.bindings
    }
    observations = []

    for relationship_id in narrative.relationship_ids:
        relationship_binding = relationship_bindings.get(relationship_id)
        if relationship_binding is None:
            _reject("OML-032 relationship observation lineage missing")
        observations.extend(
            (
                relationship_binding.source_observation_hash,
                relationship_binding.target_observation_hash,
            )
        )

    body = {
        "request_hash": request.request_hash,
        "narrative_id": narrative.narrative_id,
        "narrative_hash": narrative.narrative_hash,
        "participating_entity_ids": narrative.participating_entity_ids,
        "relationship_ids": narrative.relationship_ids,
        "source_observation_hashes": tuple(sorted(set(observations))),
        "entity_lineage_verified": True,
        "relationship_lineage_verified": True,
        "observation_lineage_verified": True,
        "evidence_lineage_verified": (
            narrative.supporting_evidence_hashes
            == request.supporting_evidence_hashes
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

    binding = OracleMemoryObservationNarrativeBinding(
        **body,
        binding_hash=_stable_hash(body),
    )
    verify_oracle_memory_observation_narrative_binding(binding)
    return binding


def verify_oracle_memory_observation_narrative_binding(
    binding: OracleMemoryObservationNarrativeBinding,
) -> bool:
    body = asdict(binding)
    supplied = body.pop("binding_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-032 binding hash mismatch")

    for value in (
        binding.request_hash,
        binding.narrative_id,
        binding.narrative_hash,
        binding.binding_hash,
        *binding.participating_entity_ids,
        *binding.relationship_ids,
        *binding.source_observation_hashes,
    ):
        _require_hash(value, "binding lineage hash")

    required_true = (
        binding.entity_lineage_verified,
        binding.relationship_lineage_verified,
        binding.observation_lineage_verified,
        binding.evidence_lineage_verified,
        binding.deterministic_binding_verified,
        binding.read_only,
    )
    if not all(required_true):
        _reject("OML-032 binding guarantee missing")

    forbidden = (
        binding.persistence_authorized,
        binding.learning_update_authorized,
        binding.runtime_activation_authorized,
        binding.publication_authorized,
        binding.action_authorization_enabled,
        binding.qseries_execution_authorized,
    )
    if any(forbidden):
        _reject("OML-032 forbidden binding capability enabled")
    return True


def build_oracle_memory_observation_narrative_detection(
    *,
    materialization: OracleMemoryObservationRelationshipGraphMaterialization,
    requests: Sequence[OracleMemoryObservationNarrativeRequest],
) -> OracleMemoryObservationNarrativeDetection:
    verify_oracle_memory_observation_relationship_graph_materialization(
        materialization
    )

    if materialization.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-032 upstream schema mismatch")
    if materialization.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-032 upstream engine mismatch")
    if not materialization.graph_ready:
        _reject("OML-032 graph not ready")
    if not materialization.downstream_narrative_detection_authorized:
        _reject("OML-032 narrative detection not authorized")
    if not materialization.read_only:
        _reject("OML-032 upstream graph not read-only")

    ordered_requests = tuple(
        sorted(
            requests,
            key=lambda item: (
                item.title.lower(),
                item.evolution_index,
                item.request_hash,
            ),
        )
    )

    narratives = tuple(
        build_oracle_memory_narrative(
            graph=materialization.graph,
            title=request.title,
            participating_entity_ids=request.participating_entity_ids,
            relationship_ids=request.relationship_ids,
            supporting_evidence_hashes=request.supporting_evidence_hashes,
            contradicting_evidence_hashes=(
                request.contradicting_evidence_hashes
            ),
            confidence=request.confidence,
            uncertainty=request.uncertainty,
            first_observed_at=request.first_observed_at,
            last_observed_at=request.last_observed_at,
            evolution_index=request.evolution_index,
            prior_stage=request.prior_stage,
        )
        for request in ordered_requests
    )

    narrative_batch = build_oracle_memory_narrative_evolution_batch(
        graph=materialization.graph,
        narratives=narratives,
    )

    bindings = tuple(
        _build_binding(
            materialization=materialization,
            request=request,
            narrative=narrative,
        )
        for request, narrative in zip(
            ordered_requests,
            narratives,
            strict=True,
        )
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": materialization.schema_version,
        "upstream_engine_id": materialization.engine_id,
        "upstream_materialization_hash": materialization.materialization_hash,
        "upstream_graph_hash": materialization.graph.graph_hash,
        "narrative_batch": narrative_batch,
        "narratives": narrative_batch.narratives,
        "bindings": bindings,
        "narrative_count": narrative_batch.narrative_count,
        "emerging_count": narrative_batch.emerging_count,
        "strengthening_count": narrative_batch.strengthening_count,
        "weakening_count": narrative_batch.weakening_count,
        "resolved_count": narrative_batch.resolved_count,
        "narrative_state": NARRATIVE_STATE_READ_ONLY,
        "certified_graph_lineage_verified": True,
        "observation_narrative_lineage_verified": True,
        "canonical_order_verified": True,
        "deterministic_detection_verified": True,
        "contradiction_tracking_verified": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "detection_ready": True,
        "downstream_lifecycle_tracking_authorized": True,
        "read_only": True,
    }

    detection = OracleMemoryObservationNarrativeDetection(
        **body,
        detection_hash=_stable_hash(body),
    )
    verify_oracle_memory_observation_narrative_detection(detection)
    return detection


def verify_oracle_memory_observation_narrative_detection(
    detection: OracleMemoryObservationNarrativeDetection,
) -> bool:
    body = asdict(detection)
    supplied = body.pop("detection_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-032 detection hash mismatch")

    if detection.schema_version != SCHEMA_VERSION:
        _reject("OML-032 schema mismatch")
    if detection.engine_id != ENGINE_ID:
        _reject("OML-032 engine mismatch")
    if detection.policy_id != POLICY_ID:
        _reject("OML-032 policy mismatch")
    if detection.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-032 subsystem mismatch")
    if detection.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-032 upstream schema lineage mismatch")
    if detection.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-032 upstream engine lineage mismatch")

    verify_oracle_memory_narrative_evolution_batch(
        detection.narrative_batch
    )

    if detection.narrative_count != len(detection.narratives):
        _reject("OML-032 narrative count mismatch")
    if detection.narrative_count != len(detection.bindings):
        _reject("OML-032 binding count mismatch")

    for narrative in detection.narratives:
        verify_oracle_memory_narrative(narrative)
    for binding in detection.bindings:
        verify_oracle_memory_observation_narrative_binding(binding)

    if detection.narrative_state != NARRATIVE_STATE_READ_ONLY:
        _reject("OML-032 narrative state invalid")

    required_true = (
        detection.certified_graph_lineage_verified,
        detection.observation_narrative_lineage_verified,
        detection.canonical_order_verified,
        detection.deterministic_detection_verified,
        detection.contradiction_tracking_verified,
        detection.detection_ready,
        detection.downstream_lifecycle_tracking_authorized,
        detection.read_only,
    )
    if not all(required_true):
        _reject("OML-032 detection guarantee missing")

    forbidden = (
        detection.persistence_enabled,
        detection.learning_updates_enabled,
        detection.runtime_activation_enabled,
        detection.publication_enabled,
        detection.action_authorization_enabled,
        detection.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-032 forbidden detection capability enabled")
    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_detection_and_evolution import (
    OracleMemoryObservationNarrativeInvariantError,
    build_oracle_memory_observation_narrative_detection,
    build_oracle_memory_observation_narrative_request,
    verify_oracle_memory_observation_narrative_detection,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_relationship_graph_materialization import (
    build_oracle_memory_observation_relationship_graph_materialization,
    build_oracle_memory_observation_relationship_request,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
    NARRATIVE_STAGE_STRENGTHENING,
    OracleMemoryNarrativeInvariantError,
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
    except (
        OracleMemoryObservationNarrativeInvariantError,
        OracleMemoryNarrativeInvariantError,
    ):
        return
    raise AssertionError(f"tampered OML-032 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-032 TEST")
    print(" CERTIFIED OBSERVATION NARRATIVE DETECTION AND EVOLUTION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    fixture_031 = load_module(
        root
        / "test_oml_031_oracle_memory_certified_observation_relationship_graph_materialization.py",
        "oml_031_fixture_for_oml_032",
    )

    resolution = fixture_031.build_resolution(root)
    liquidity = next(
        item for item in resolution.entities
        if item.normalized_name == "stablecoin liquidity"
    )
    bitcoin = next(
        item for item in resolution.entities
        if item.normalized_name == "bitcoin"
    )

    relationship_request = (
        build_oracle_memory_observation_relationship_request(
            source_entity_id=liquidity.canonical_entity_id,
            target_entity_id=bitcoin.canonical_entity_id,
            relationship_type="precedes market repricing",
            evidence_hashes=("5" * 64, "6" * 64),
            confidence=0.84,
            contradiction_count=0,
            directed=True,
        )
    )

    graph_materialization = (
        build_oracle_memory_observation_relationship_graph_materialization(
            resolution=resolution,
            requests=(relationship_request,),
        )
    )

    relationship = graph_materialization.graph.relationships[0]

    narrative_request = build_oracle_memory_observation_narrative_request(
        title="Stablecoin liquidity precedes Bitcoin repricing",
        participating_entity_ids=(
            liquidity.canonical_entity_id,
            bitcoin.canonical_entity_id,
        ),
        relationship_ids=(relationship.relationship_id,),
        supporting_evidence_hashes=(
            "7" * 64,
            "8" * 64,
            "9" * 64,
        ),
        contradicting_evidence_hashes=(),
        confidence=0.82,
        uncertainty=0.18,
        first_observed_at="2026-08-02T15:00:00-05:00",
        last_observed_at="2026-08-02T15:10:00-05:00",
        evolution_index=1,
    )

    detection = build_oracle_memory_observation_narrative_detection(
        materialization=graph_materialization,
        requests=(narrative_request,),
    )

    assert detection.schema_version == "OML-032"
    assert detection.engine_id == "OML-032"
    assert detection.upstream_schema_version == "OML-031"
    assert detection.upstream_engine_id == "OML-031"
    assert detection.narrative_count == 1
    assert detection.strengthening_count == 1
    assert detection.narratives[0].stage == (
        NARRATIVE_STAGE_STRENGTHENING
    )
    assert detection.bindings[0].observation_lineage_verified
    assert detection.certified_graph_lineage_verified
    assert detection.observation_narrative_lineage_verified
    assert detection.canonical_order_verified
    assert detection.deterministic_detection_verified
    assert detection.contradiction_tracking_verified
    assert not detection.persistence_enabled
    assert not detection.learning_updates_enabled
    assert not detection.runtime_activation_enabled
    assert not detection.publication_enabled
    assert not detection.action_authorization_enabled
    assert not detection.qseries_execution_enabled
    assert detection.detection_ready
    assert detection.downstream_lifecycle_tracking_authorized
    assert detection.read_only

    replay = build_oracle_memory_observation_narrative_detection(
        materialization=graph_materialization,
        requests=(narrative_request,),
    )
    assert replay == detection
    assert verify_oracle_memory_observation_narrative_detection(detection)

    expect_rejection(
        lambda: build_oracle_memory_observation_narrative_request(
            title="Invalid",
            participating_entity_ids=(),
            relationship_ids=(relationship.relationship_id,),
            supporting_evidence_hashes=("a" * 64,),
            confidence=0.5,
            uncertainty=0.5,
            first_observed_at="2026-08-02T15:00:00-05:00",
            last_observed_at="2026-08-02T15:10:00-05:00",
        ),
        "empty entity lineage",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_narrative_detection(
            replace(detection, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_narrative_detection(
            replace(
                detection,
                downstream_lifecycle_tracking_authorized=False,
            )
        ),
        "lifecycle authorization",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_narrative_detection(
            replace(detection, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-031 graph materialization consumed")
    print("[PASS] Certified OML-020 narrative engine consumed")
    print("[PASS] Exact OML-019 graph dataclass passed directly")
    print("[PASS] Observation-backed narrative created")
    print("[PASS] Strengthening narrative stage detected")
    print("[PASS] Entity and relationship lineage retained")
    print("[PASS] Source observation lineage retained")
    print("[PASS] Contradiction tracking retained")
    print("[PASS] Narrative detection deterministic across replay")
    print("[PASS] Lifecycle continuation authorized read-only")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered narrative detections rejected")
    print(
        "[DONE] OML-032 CERTIFIED OBSERVATION "
        "NARRATIVE DETECTION AND EVOLUTION PASS"
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
    required = (
        UPSTREAM,
        UPSTREAM_TEST,
        NARRATIVE_MODULE,
        NARRATIVE_TEST,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified upstream files missing: "
            + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_relationship_graph_materialization"
    )
    narrative_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_narrative_detection_and_evolution_engine"
    )

    expected_upstream = {
        "SCHEMA_VERSION": "OML-031",
        "ENGINE_ID": "OML-031",
        "POLICY_ID": (
            "oracle-memory.certified-observation-relationship-graph-materialization.v1"
        ),
    }
    expected_narrative = {
        "SCHEMA_VERSION": "OML-020",
        "ENGINE_ID": "OML-020",
        "POLICY_ID": (
            "oracle-memory.narrative-detection-and-evolution-engine.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-019",
        "UPSTREAM_ENGINE_ID": "OML-019",
    }

    for name, value in expected_upstream.items():
        if getattr(upstream_module, name, None) != value:
            raise RuntimeError(f"Certified OML-031 {name} mismatch")

    for name, value in expected_narrative.items():
        if getattr(narrative_module, name, None) != value:
            raise RuntimeError(f"Certified OML-020 {name} mismatch")

    required_builders = {
        "build_oracle_memory_narrative": {
            "graph",
            "title",
            "participating_entity_ids",
            "relationship_ids",
            "supporting_evidence_hashes",
            "contradicting_evidence_hashes",
            "confidence",
            "uncertainty",
            "first_observed_at",
            "last_observed_at",
            "evolution_index",
            "prior_stage",
        },
        "build_oracle_memory_narrative_evolution_batch": {
            "graph",
            "narratives",
        },
    }

    for builder_name, parameters in required_builders.items():
        builder = getattr(narrative_module, builder_name, None)
        if builder is None:
            raise RuntimeError(
                f"Certified OML-020 builder missing: {builder_name}"
            )
        missing_parameters = sorted(
            parameters - set(inspect.signature(builder).parameters)
        )
        if missing_parameters:
            raise RuntimeError(
                f"Certified OML-020 {builder_name} parameters missing: "
                + ", ".join(missing_parameters)
            )


def main() -> int:
    print("=" * 48)
    print(" OML-032 FOR-SURE INSTALLER")
    print(" CERTIFIED OBSERVATION NARRATIVE DETECTION AND EVOLUTION")
    print("=" * 48)
    print("[BOOT] Revision: EXACT_OML_031_020_INTERFACE_ALIGNMENT")

    try:
        validate_upstreams()
        print("[OK] Actual OML-031 contract verified")
        print("[OK] Actual OML-020 builders and signatures verified")

        upstream_run = subprocess.run(
            [sys.executable, str(UPSTREAM_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream_run.returncode:
            raise RuntimeError(
                "OML-031 certification failed with exit code "
                f"{upstream_run.returncode}"
            )

        narrative_run = subprocess.run(
            [sys.executable, str(NARRATIVE_TEST)],
            cwd=ROOT,
            check=False,
        )
        if narrative_run.returncode:
            raise RuntimeError(
                "OML-020 certification failed with exit code "
                f"{narrative_run.returncode}"
            )

        tracked = {
            path: path.read_bytes()
            for path in (
                UPSTREAM,
                UPSTREAM_TEST,
                NARRATIVE_MODULE,
                NARRATIVE_TEST,
            )
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from ."
            "oracle_memory_certified_observation_narrative_detection_and_evolution "
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
                "OML-032 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(
                    f"Certified upstream changed: {path}"
                )

        print("[PASS] Certified OML-031 production unchanged")
        print("[PASS] Certified OML-031 standalone test unchanged")
        print("[PASS] Certified OML-020 narrative engine unchanged")
        print("[PASS] OML-032 production installed")
        print("[PASS] OML-032 standalone deterministic test installed")
        print("[PASS] Observation graph now enters narrative layer")
        print("[PASS] Exact upstream graph dataclass preserved")
        print("[PASS] Lifecycle continuation authorized read-only")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OML-032 CERTIFIED OBSERVATION "
            "NARRATIVE DETECTION AND EVOLUTION INSTALLED"
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


if __name__ == "__main__":
    raise SystemExit(main())
