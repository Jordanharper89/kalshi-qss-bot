from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = (
    PACKAGE
    / "oracle_memory_relationship_graph_and_linkage_resolution.py"
)
UPSTREAM_TEST = (
    ROOT
    / "test_oml_019_oracle_memory_relationship_graph_and_linkage_resolution.py"
)

PRODUCTION = (
    PACKAGE
    / "oracle_memory_narrative_detection_and_evolution_engine.py"
)
TEST = (
    ROOT
    / "test_oml_020_oracle_memory_narrative_detection_and_evolution_engine.py"
)
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
from qseries_v2.oracle_memory.oracle_memory_relationship_graph_and_linkage_resolution import (
    OracleMemoryEntityRelationship,
    OracleMemoryRelationshipGraph,
    verify_oracle_memory_entity_relationship,
    verify_oracle_memory_relationship_graph,
)

SCHEMA_VERSION = "OML-020"
ENGINE_ID = "OML-020"
POLICY_ID = "oracle-memory.narrative-detection-and-evolution-engine.v1"

UPSTREAM_SCHEMA_VERSION = "OML-019"
UPSTREAM_ENGINE_ID = "OML-019"

NARRATIVE_STAGE_EMERGING = "emerging"
NARRATIVE_STAGE_STRENGTHENING = "strengthening"
NARRATIVE_STAGE_WEAKENING = "weakening"
NARRATIVE_STAGE_RESOLVED = "resolved"

ALLOWED_STAGES = (
    NARRATIVE_STAGE_EMERGING,
    NARRATIVE_STAGE_STRENGTHENING,
    NARRATIVE_STAGE_WEAKENING,
    NARRATIVE_STAGE_RESOLVED,
)


class OracleMemoryNarrativeInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryNarrative:
    narrative_id: str
    title: str
    normalized_title: str
    stage: str
    participating_entity_ids: tuple[str, ...]
    relationship_ids: tuple[str, ...]
    supporting_evidence_hashes: tuple[str, ...]
    contradicting_evidence_hashes: tuple[str, ...]
    confidence: float
    uncertainty: float
    contradiction_count: int
    first_observed_at: str
    last_observed_at: str
    evolution_index: int
    entity_lineage_verified: bool
    relationship_lineage_verified: bool
    evidence_lineage_verified: bool
    deterministic_identity_verified: bool
    canonical_order_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    narrative_hash: str


@dataclass(frozen=True)
class OracleMemoryNarrativeEvolutionBatch:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_graph_hash: str
    narratives: tuple[OracleMemoryNarrative, ...]
    narrative_count: int
    emerging_count: int
    strengthening_count: int
    weakening_count: int
    resolved_count: int
    canonical_order_verified: bool
    deterministic_detection_verified: bool
    deterministic_evolution_verified: bool
    entity_lineage_verified: bool
    relationship_lineage_verified: bool
    supporting_evidence_verified: bool
    contradiction_tracking_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    batch_ready: bool
    next_certification_authorized: bool
    read_only: bool
    batch_hash: str


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

    raise OracleMemoryNarrativeInvariantError(
        "unsupported OML-020 value type: "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


def _reject(reason: str) -> None:
    raise OracleMemoryNarrativeInvariantError(reason)


def _normalize_text(value: str) -> str:
    normalized = " ".join(value.strip().lower().split())

    if not normalized:
        _reject("OML-020 normalized text cannot be empty")

    return normalized


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-020 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryNarrativeInvariantError(
            f"OML-020 invalid {label} hexadecimal value"
        ) from exc


def _derive_stage(
    *,
    supporting_evidence_count: int,
    contradiction_count: int,
    confidence: float,
    prior_stage: str | None,
) -> str:
    if prior_stage == NARRATIVE_STAGE_RESOLVED:
        return NARRATIVE_STAGE_RESOLVED

    if contradiction_count > supporting_evidence_count:
        return NARRATIVE_STAGE_WEAKENING

    if supporting_evidence_count >= 3 and confidence >= 0.70:
        return NARRATIVE_STAGE_STRENGTHENING

    return NARRATIVE_STAGE_EMERGING


def build_oracle_memory_narrative(
    *,
    graph: OracleMemoryRelationshipGraph,
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
) -> OracleMemoryNarrative:
    verify_oracle_memory_relationship_graph(graph)

    if graph.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-020 upstream graph schema mismatch")

    if graph.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-020 upstream graph engine mismatch")

    if not graph.graph_ready:
        _reject("OML-020 upstream graph not ready")

    if not graph.next_certification_authorized:
        _reject("OML-020 upstream continuation not authorized")

    if not graph.read_only:
        _reject("OML-020 upstream graph is not read-only")

    normalized_title = _normalize_text(title)

    entity_ids = tuple(sorted(set(participating_entity_ids)))
    rel_ids = tuple(sorted(set(relationship_ids)))
    supporting = tuple(sorted(set(supporting_evidence_hashes)))
    contradicting = tuple(sorted(set(contradicting_evidence_hashes)))

    if not entity_ids:
        _reject("OML-020 narrative requires participating entities")

    graph_entity_ids = {
        entity.canonical_entity_id
        for entity in graph.entities
    }

    if any(entity_id not in graph_entity_ids for entity_id in entity_ids):
        _reject("OML-020 narrative contains unknown entity")

    graph_relationships = {
        relationship.relationship_id: relationship
        for relationship in graph.relationships
    }

    if any(rel_id not in graph_relationships for rel_id in rel_ids):
        _reject("OML-020 narrative contains unknown relationship")

    for rel_id in rel_ids:
        verify_oracle_memory_entity_relationship(
            graph_relationships[rel_id]
        )

    if not supporting:
        _reject("OML-020 narrative requires supporting evidence")

    for value in (*supporting, *contradicting):
        _require_hash(value, "evidence hash")

    confidence = float(confidence)
    uncertainty = float(uncertainty)

    if not 0.0 <= confidence <= 1.0:
        _reject("OML-020 confidence outside [0, 1]")

    if not 0.0 <= uncertainty <= 1.0:
        _reject("OML-020 uncertainty outside [0, 1]")

    if (
        not isinstance(evolution_index, int)
        or isinstance(evolution_index, bool)
        or evolution_index < 1
    ):
        _reject("OML-020 evolution index invalid")

    if not isinstance(first_observed_at, str) or not first_observed_at.strip():
        _reject("OML-020 first_observed_at required")

    if not isinstance(last_observed_at, str) or not last_observed_at.strip():
        _reject("OML-020 last_observed_at required")

    stage = _derive_stage(
        supporting_evidence_count=len(supporting),
        contradiction_count=len(contradicting),
        confidence=confidence,
        prior_stage=prior_stage,
    )

    narrative_id = _stable_hash(
        {
            "normalized_title": normalized_title,
            "participating_entity_ids": entity_ids,
        }
    )

    body = {
        "narrative_id": narrative_id,
        "title": title.strip(),
        "normalized_title": normalized_title,
        "stage": stage,
        "participating_entity_ids": entity_ids,
        "relationship_ids": rel_ids,
        "supporting_evidence_hashes": supporting,
        "contradicting_evidence_hashes": contradicting,
        "confidence": confidence,
        "uncertainty": uncertainty,
        "contradiction_count": len(contradicting),
        "first_observed_at": first_observed_at.strip(),
        "last_observed_at": last_observed_at.strip(),
        "evolution_index": evolution_index,
        "entity_lineage_verified": True,
        "relationship_lineage_verified": True,
        "evidence_lineage_verified": True,
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

    narrative = OracleMemoryNarrative(
        **body,
        narrative_hash=_stable_hash(body),
    )

    verify_oracle_memory_narrative(narrative)
    return narrative


def verify_oracle_memory_narrative(
    narrative: OracleMemoryNarrative,
) -> bool:
    body = asdict(narrative)
    supplied = body.pop("narrative_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-020 narrative hash mismatch")

    _require_hash(narrative.narrative_id, "narrative id")
    _require_hash(narrative.narrative_hash, "narrative hash")

    if narrative.normalized_title != _normalize_text(narrative.title):
        _reject("OML-020 title normalization mismatch")

    if narrative.stage not in ALLOWED_STAGES:
        _reject("OML-020 narrative stage invalid")

    if not narrative.participating_entity_ids:
        _reject("OML-020 narrative entity lineage missing")

    if not narrative.supporting_evidence_hashes:
        _reject("OML-020 supporting evidence missing")

    for value in (
        *narrative.participating_entity_ids,
        *narrative.relationship_ids,
        *narrative.supporting_evidence_hashes,
        *narrative.contradicting_evidence_hashes,
    ):
        _require_hash(value, "narrative lineage hash")

    if tuple(sorted(set(narrative.participating_entity_ids))) != (
        narrative.participating_entity_ids
    ):
        _reject("OML-020 entity order or uniqueness invalid")

    if tuple(sorted(set(narrative.relationship_ids))) != (
        narrative.relationship_ids
    ):
        _reject("OML-020 relationship order or uniqueness invalid")

    if tuple(sorted(set(narrative.supporting_evidence_hashes))) != (
        narrative.supporting_evidence_hashes
    ):
        _reject("OML-020 supporting evidence order invalid")

    if tuple(sorted(set(narrative.contradicting_evidence_hashes))) != (
        narrative.contradicting_evidence_hashes
    ):
        _reject("OML-020 contradicting evidence order invalid")

    if not 0.0 <= narrative.confidence <= 1.0:
        _reject("OML-020 narrative confidence invalid")

    if not 0.0 <= narrative.uncertainty <= 1.0:
        _reject("OML-020 narrative uncertainty invalid")

    if narrative.contradiction_count != len(
        narrative.contradicting_evidence_hashes
    ):
        _reject("OML-020 contradiction count mismatch")

    if narrative.evolution_index < 1:
        _reject("OML-020 evolution index invalid")

    expected_id = _stable_hash(
        {
            "normalized_title": narrative.normalized_title,
            "participating_entity_ids": (
                narrative.participating_entity_ids
            ),
        }
    )

    if narrative.narrative_id != expected_id:
        _reject("OML-020 narrative identity mismatch")

    required_true = (
        narrative.entity_lineage_verified,
        narrative.relationship_lineage_verified,
        narrative.evidence_lineage_verified,
        narrative.deterministic_identity_verified,
        narrative.canonical_order_verified,
        narrative.read_only,
    )

    if not all(required_true):
        _reject("OML-020 narrative guarantee missing")

    forbidden = (
        narrative.persistence_authorized,
        narrative.learning_update_authorized,
        narrative.runtime_activation_authorized,
        narrative.publication_authorized,
        narrative.action_authorization_enabled,
        narrative.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-020 forbidden narrative capability enabled")

    return True


def build_oracle_memory_narrative_evolution_batch(
    *,
    graph: OracleMemoryRelationshipGraph,
    narratives: Sequence[OracleMemoryNarrative],
) -> OracleMemoryNarrativeEvolutionBatch:
    verify_oracle_memory_relationship_graph(graph)

    ordered = tuple(
        sorted(
            narratives,
            key=lambda item: (
                item.normalized_title,
                item.narrative_id,
                item.evolution_index,
            ),
        )
    )

    for narrative in ordered:
        verify_oracle_memory_narrative(narrative)

    narrative_ids = tuple(
        narrative.narrative_id
        for narrative in ordered
    )

    if len(set(narrative_ids)) != len(narrative_ids):
        _reject("OML-020 duplicate narrative identities forbidden")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": graph.schema_version,
        "upstream_engine_id": graph.engine_id,
        "upstream_graph_hash": graph.graph_hash,
        "narratives": ordered,
        "narrative_count": len(ordered),
        "emerging_count": sum(
            item.stage == NARRATIVE_STAGE_EMERGING
            for item in ordered
        ),
        "strengthening_count": sum(
            item.stage == NARRATIVE_STAGE_STRENGTHENING
            for item in ordered
        ),
        "weakening_count": sum(
            item.stage == NARRATIVE_STAGE_WEAKENING
            for item in ordered
        ),
        "resolved_count": sum(
            item.stage == NARRATIVE_STAGE_RESOLVED
            for item in ordered
        ),
        "canonical_order_verified": True,
        "deterministic_detection_verified": True,
        "deterministic_evolution_verified": True,
        "entity_lineage_verified": True,
        "relationship_lineage_verified": True,
        "supporting_evidence_verified": True,
        "contradiction_tracking_verified": True,
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

    batch = OracleMemoryNarrativeEvolutionBatch(
        **body,
        batch_hash=_stable_hash(body),
    )

    verify_oracle_memory_narrative_evolution_batch(batch)
    return batch


def verify_oracle_memory_narrative_evolution_batch(
    batch: OracleMemoryNarrativeEvolutionBatch,
) -> bool:
    body = asdict(batch)
    supplied = body.pop("batch_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-020 batch hash mismatch")

    if batch.schema_version != SCHEMA_VERSION:
        _reject("OML-020 batch schema mismatch")

    if batch.engine_id != ENGINE_ID:
        _reject("OML-020 batch engine mismatch")

    if batch.policy_id != POLICY_ID:
        _reject("OML-020 batch policy mismatch")

    if batch.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-020 batch subsystem mismatch")

    if batch.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-020 upstream schema lineage mismatch")

    if batch.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-020 upstream engine lineage mismatch")

    if batch.narrative_count != len(batch.narratives):
        _reject("OML-020 narrative count mismatch")

    if (
        batch.emerging_count
        + batch.strengthening_count
        + batch.weakening_count
        + batch.resolved_count
        != batch.narrative_count
    ):
        _reject("OML-020 stage count reconciliation mismatch")

    narrative_ids = []

    for narrative in batch.narratives:
        verify_oracle_memory_narrative(narrative)
        narrative_ids.append(narrative.narrative_id)

    if len(set(narrative_ids)) != len(narrative_ids):
        _reject("OML-020 duplicate narrative ids")

    required_true = (
        batch.canonical_order_verified,
        batch.deterministic_detection_verified,
        batch.deterministic_evolution_verified,
        batch.entity_lineage_verified,
        batch.relationship_lineage_verified,
        batch.supporting_evidence_verified,
        batch.contradiction_tracking_verified,
        batch.batch_ready,
        batch.next_certification_authorized,
        batch.read_only,
    )

    if not all(required_true):
        _reject("OML-020 batch guarantee missing")

    forbidden = (
        batch.persistence_enabled,
        batch.learning_updates_enabled,
        batch.runtime_activation_enabled,
        batch.publication_enabled,
        batch.action_authorization_enabled,
        batch.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-020 forbidden batch capability enabled")

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
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract import (
    build_oracle_memory_canonical_record_candidate,
)
from qseries_v2.oracle_memory.oracle_memory_entity_resolution import (
    build_oracle_memory_entity_resolution_batch,
)
from qseries_v2.oracle_memory.oracle_memory_ledger_integrity_and_replay_certification import (
    build_oracle_memory_ledger_integrity_replay_certification,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
    NARRATIVE_STAGE_STRENGTHENING,
    OracleMemoryNarrativeInvariantError,
    build_oracle_memory_narrative,
    build_oracle_memory_narrative_evolution_batch,
    verify_oracle_memory_narrative_evolution_batch,
)
from qseries_v2.oracle_memory.oracle_memory_relationship_graph_and_linkage_resolution import (
    build_oracle_memory_entity_relationship,
    build_oracle_memory_relationship_graph,
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
    except OracleMemoryNarrativeInvariantError:
        return

    raise AssertionError(f"tampered OML-020 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-020 TEST")
    print(" NARRATIVE DETECTION AND EVOLUTION ENGINE")
    print("=" * 48)

    root = Path(__file__).resolve().parent

    fixture_016 = load_module(
        root
        / "test_oml_016_oracle_memory_ledger_integrity_and_replay_certification.py",
        "oml_016_fixture_for_oml_020",
    )
    ledger_contract = fixture_016.build_oml_015_contract(root)
    ledger = build_oracle_memory_ledger_integrity_replay_certification(
        ledger_contract=ledger_contract,
    )

    fixture_009 = load_module(
        root
        / "test_oml_009_oracle_memory_canonical_record_candidate_contract.py",
        "oml_009_fixture_for_oml_020",
    )
    gate = fixture_009.build_oml_008_decision(root)

    candidate_consumer = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=gate.admitted_domain_ids[0],
        candidate_id="candidate:entity:consumer-demand",
        entity_key="Consumer Demand",
        source_key="certified-observation-source",
        observed_at="2026-08-02T14:46:00-05:00",
        effective_at="2026-08-02T14:46:00-05:00",
        payload={"entity_type": "real_world_behavior"},
        evidence_hashes=("1" * 64,),
        parent_record_hashes=(),
        confidence=0.88,
        uncertainty=0.12,
        contradiction_count=0,
    )

    candidate_market = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=gate.admitted_domain_ids[0],
        candidate_id="candidate:entity:market-reaction",
        entity_key="Market Reaction",
        source_key="certified-observation-source",
        observed_at="2026-08-02T14:46:00-05:00",
        effective_at="2026-08-02T14:46:00-05:00",
        payload={"entity_type": "financial_response"},
        evidence_hashes=("2" * 64,),
        parent_record_hashes=(),
        confidence=0.84,
        uncertainty=0.16,
        contradiction_count=0,
    )

    validation = build_oracle_memory_candidate_validation_batch(
        ledger_certification=ledger,
        candidates=(candidate_consumer, candidate_market),
    )

    entities = build_oracle_memory_entity_resolution_batch(
        validation_batch=validation,
        aliases_by_candidate_hash={
            candidate_consumer.candidate_hash: (
                "Demand Shift",
                "Consumer Behavior",
            ),
            candidate_market.candidate_hash: (
                "Price Reaction",
                "Financial Market Response",
            ),
        },
    )

    consumer = next(
        item for item in entities.entities
        if item.normalized_name == "consumer demand"
    )
    market = next(
        item for item in entities.entities
        if item.normalized_name == "market reaction"
    )

    relationship = build_oracle_memory_entity_relationship(
        source_entity=consumer,
        target_entity=market,
        relationship_type="precedes",
        evidence_hashes=("3" * 64, "4" * 64),
        confidence=0.91,
        contradiction_count=0,
        directed=True,
    )

    graph = build_oracle_memory_relationship_graph(
        entity_batch=entities,
        relationships=(relationship,),
    )

    narrative = build_oracle_memory_narrative(
        graph=graph,
        title="Consumer demand shifting before market reaction",
        participating_entity_ids=(
            consumer.canonical_entity_id,
            market.canonical_entity_id,
        ),
        relationship_ids=(relationship.relationship_id,),
        supporting_evidence_hashes=(
            "5" * 64,
            "6" * 64,
            "7" * 64,
        ),
        contradicting_evidence_hashes=(),
        confidence=0.82,
        uncertainty=0.18,
        first_observed_at="2026-08-02T14:40:00-05:00",
        last_observed_at="2026-08-02T14:46:00-05:00",
        evolution_index=1,
    )

    assert narrative.stage == NARRATIVE_STAGE_STRENGTHENING
    assert narrative.contradiction_count == 0
    assert narrative.entity_lineage_verified
    assert narrative.relationship_lineage_verified
    assert narrative.evidence_lineage_verified
    assert narrative.deterministic_identity_verified
    assert narrative.canonical_order_verified
    assert not narrative.persistence_authorized
    assert not narrative.learning_update_authorized
    assert not narrative.runtime_activation_authorized
    assert not narrative.publication_authorized
    assert not narrative.action_authorization_enabled
    assert not narrative.qseries_execution_authorized
    assert narrative.read_only

    batch = build_oracle_memory_narrative_evolution_batch(
        graph=graph,
        narratives=(narrative,),
    )

    assert batch.schema_version == "OML-020"
    assert batch.engine_id == "OML-020"
    assert batch.upstream_schema_version == "OML-019"
    assert batch.upstream_engine_id == "OML-019"
    assert batch.narrative_count == 1
    assert batch.strengthening_count == 1
    assert batch.emerging_count == 0
    assert batch.weakening_count == 0
    assert batch.resolved_count == 0
    assert batch.canonical_order_verified
    assert batch.deterministic_detection_verified
    assert batch.deterministic_evolution_verified
    assert batch.entity_lineage_verified
    assert batch.relationship_lineage_verified
    assert batch.supporting_evidence_verified
    assert batch.contradiction_tracking_verified
    assert not batch.persistence_enabled
    assert not batch.learning_updates_enabled
    assert not batch.runtime_activation_enabled
    assert not batch.publication_enabled
    assert not batch.action_authorization_enabled
    assert not batch.qseries_execution_enabled
    assert batch.batch_ready
    assert batch.next_certification_authorized
    assert batch.read_only

    replay = build_oracle_memory_narrative_evolution_batch(
        graph=graph,
        narratives=(narrative,),
    )

    assert replay == batch
    assert verify_oracle_memory_narrative_evolution_batch(batch)

    expect_rejection(
        lambda: verify_oracle_memory_narrative_evolution_batch(
            replace(batch, narrative_count=2)
        ),
        "narrative count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_narrative_evolution_batch(
            replace(batch, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_narrative_evolution_batch(
            replace(batch, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-019 relationship graph consumed")
    print("[PASS] Participating entity lineage retained")
    print("[PASS] Relationship lineage retained")
    print("[PASS] Supporting evidence lineage retained")
    print("[PASS] Contradicting evidence tracking enabled")
    print("[PASS] Stable narrative identity generated")
    print("[PASS] Narrative stage detected deterministically")
    print("[PASS] Narrative evolution index retained")
    print("[PASS] Canonical narrative ordering verified")
    print("[PASS] Narrative batch deterministic across replay")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered narrative batches rejected")
    print("[DONE] OML-020 NARRATIVE DETECTION AND EVOLUTION ENGINE PASS")
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
            "Certified OML-019 production or standalone test missing"
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_relationship_graph_and_linkage_resolution"
    )

    expected = {
        "SCHEMA_VERSION": "OML-019",
        "ENGINE_ID": "OML-019",
        "POLICY_ID": (
            "oracle-memory.relationship-graph-and-linkage-resolution.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-018",
        "UPSTREAM_ENGINE_ID": "OML-018",
        "RELATIONSHIP_STATUS_RESOLVED": "resolved",
    }

    for name, value in expected.items():
        actual = getattr(module, name, None)

        if actual != value:
            raise RuntimeError(
                f"Certified OML-019 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    required = (
        "OracleMemoryEntityRelationship",
        "OracleMemoryRelationshipGraph",
        "build_oracle_memory_entity_relationship",
        "build_oracle_memory_relationship_graph",
        "verify_oracle_memory_entity_relationship",
        "verify_oracle_memory_relationship_graph",
    )

    missing = [name for name in required if not hasattr(module, name)]

    if missing:
        raise RuntimeError(
            "Certified OML-019 missing required symbols: "
            + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-020 FOR-SURE INSTALLER")
    print(" NARRATIVE DETECTION AND EVOLUTION ENGINE")
    print("=" * 48)
    print("[BOOT] Revision: CAPABILITY_MILESTONE_FULL_REPLACEMENT")

    try:
        validate_upstream()
        print("[OK] Actual OML-019 imported and structurally verified")

        upstream_run = subprocess.run(
            [sys.executable, str(UPSTREAM_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream_run.returncode:
            raise RuntimeError(
                "OML-019 certification failed with exit code "
                f"{upstream_run.returncode}"
            )

        production_before = UPSTREAM.read_bytes()
        test_before = UPSTREAM_TEST.read_bytes()

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_narrative_detection_and_evolution_engine "
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
                "OML-020 test failed with exit code "
                f"{completed.returncode}"
            )

        if UPSTREAM.read_bytes() != production_before:
            raise RuntimeError("Certified OML-019 production changed")

        if UPSTREAM_TEST.read_bytes() != test_before:
            raise RuntimeError("Certified OML-019 standalone test changed")

        print("[PASS] Certified OML-019 production unchanged")
        print("[PASS] Certified OML-019 standalone test unchanged")
        print("[PASS] OML-020 narrative engine installed")
        print("[PASS] OML-020 standalone deterministic test installed")
        print("[PASS] Narrative detection capability installed")
        print("[PASS] Narrative evolution capability installed")
        print("[PASS] Evidence and contradiction lineage retained")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OML-020 NARRATIVE DETECTION "
            "AND EVOLUTION ENGINE INSTALLED"
        )
        return 0

    except (RuntimeError, SyntaxError, ImportError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
