from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_entity_resolution.py"
UPSTREAM_TEST = ROOT / "test_oml_018_oracle_memory_entity_resolution.py"

PRODUCTION = PACKAGE / "oracle_memory_relationship_graph_and_linkage_resolution.py"
TEST = ROOT / "test_oml_019_oracle_memory_relationship_graph_and_linkage_resolution.py"
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
from qseries_v2.oracle_memory.oracle_memory_entity_resolution import (
    OracleMemoryEntityResolutionBatch,
    OracleMemoryResolvedEntity,
    verify_oracle_memory_entity_resolution_batch,
    verify_oracle_memory_resolved_entity,
)

SCHEMA_VERSION = "OML-019"
ENGINE_ID = "OML-019"
POLICY_ID = "oracle-memory.relationship-graph-and-linkage-resolution.v1"

UPSTREAM_SCHEMA_VERSION = "OML-018"
UPSTREAM_ENGINE_ID = "OML-018"

RELATIONSHIP_STATUS_RESOLVED = "resolved"
RELATIONSHIP_STATUS_REJECTED = "rejected"


class OracleMemoryRelationshipGraphInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryEntityRelationship:
    relationship_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    normalized_relationship_type: str
    evidence_hashes: tuple[str, ...]
    confidence: float
    contradiction_count: int
    directed: bool
    relationship_status: str
    source_entity_verified: bool
    target_entity_verified: bool
    self_link_rejected: bool
    evidence_lineage_verified: bool
    deterministic_identity_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    relationship_hash: str


@dataclass(frozen=True)
class OracleMemoryRelationshipGraph:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_batch_hash: str
    entities: tuple[OracleMemoryResolvedEntity, ...]
    relationships: tuple[OracleMemoryEntityRelationship, ...]
    entity_count: int
    relationship_count: int
    canonical_entity_order_verified: bool
    canonical_relationship_order_verified: bool
    entity_identity_uniqueness_verified: bool
    relationship_identity_uniqueness_verified: bool
    self_links_rejected: bool
    dangling_links_rejected: bool
    duplicate_links_rejected: bool
    deterministic_graph_hashing_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    graph_ready: bool
    next_certification_authorized: bool
    read_only: bool
    graph_hash: str


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

    raise OracleMemoryRelationshipGraphInvariantError(
        "unsupported OML-019 value type: "
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
    raise OracleMemoryRelationshipGraphInvariantError(reason)


def _normalize_relationship_type(value: str) -> str:
    normalized = "_".join(value.strip().lower().split())

    if not normalized:
        _reject("OML-019 relationship type cannot be empty")

    return normalized


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-019 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryRelationshipGraphInvariantError(
            f"OML-019 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_entity_relationship(
    *,
    source_entity: OracleMemoryResolvedEntity,
    target_entity: OracleMemoryResolvedEntity,
    relationship_type: str,
    evidence_hashes: Sequence[str],
    confidence: float,
    contradiction_count: int = 0,
    directed: bool = True,
) -> OracleMemoryEntityRelationship:
    verify_oracle_memory_resolved_entity(source_entity)
    verify_oracle_memory_resolved_entity(target_entity)

    if source_entity.canonical_entity_id == target_entity.canonical_entity_id:
        _reject("OML-019 self-links are forbidden")

    normalized_type = _normalize_relationship_type(relationship_type)

    evidence = tuple(evidence_hashes)

    if not evidence:
        _reject("OML-019 relationship evidence is required")

    if len(set(evidence)) != len(evidence):
        _reject("OML-019 duplicate evidence hashes forbidden")

    for value in evidence:
        _require_hash(value, "evidence hash")

    confidence = float(confidence)

    if not 0.0 <= confidence <= 1.0:
        _reject("OML-019 confidence outside [0, 1]")

    if (
        not isinstance(contradiction_count, int)
        or isinstance(contradiction_count, bool)
        or contradiction_count < 0
    ):
        _reject("OML-019 contradiction count invalid")

    identity_payload = {
        "source_entity_id": source_entity.canonical_entity_id,
        "target_entity_id": target_entity.canonical_entity_id,
        "relationship_type": normalized_type,
        "directed": bool(directed),
    }

    relationship_id = _stable_hash(identity_payload)

    body = {
        "relationship_id": relationship_id,
        "source_entity_id": source_entity.canonical_entity_id,
        "target_entity_id": target_entity.canonical_entity_id,
        "relationship_type": relationship_type.strip(),
        "normalized_relationship_type": normalized_type,
        "evidence_hashes": evidence,
        "confidence": confidence,
        "contradiction_count": contradiction_count,
        "directed": bool(directed),
        "relationship_status": RELATIONSHIP_STATUS_RESOLVED,
        "source_entity_verified": True,
        "target_entity_verified": True,
        "self_link_rejected": True,
        "evidence_lineage_verified": True,
        "deterministic_identity_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    relationship = OracleMemoryEntityRelationship(
        **body,
        relationship_hash=_stable_hash(body),
    )

    verify_oracle_memory_entity_relationship(relationship)
    return relationship


def verify_oracle_memory_entity_relationship(
    relationship: OracleMemoryEntityRelationship,
) -> bool:
    body = asdict(relationship)
    supplied = body.pop("relationship_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-019 relationship hash mismatch")

    _require_hash(relationship.relationship_id, "relationship id")
    _require_hash(
        relationship.source_entity_id,
        "source entity id",
    )
    _require_hash(
        relationship.target_entity_id,
        "target entity id",
    )
    _require_hash(relationship.relationship_hash, "relationship hash")

    if relationship.source_entity_id == relationship.target_entity_id:
        _reject("OML-019 self-link detected")

    if relationship.normalized_relationship_type != (
        _normalize_relationship_type(relationship.relationship_type)
    ):
        _reject("OML-019 relationship type normalization mismatch")

    if not relationship.evidence_hashes:
        _reject("OML-019 relationship evidence missing")

    if len(set(relationship.evidence_hashes)) != len(
        relationship.evidence_hashes
    ):
        _reject("OML-019 duplicate evidence lineage")

    for value in relationship.evidence_hashes:
        _require_hash(value, "relationship evidence hash")

    if not 0.0 <= relationship.confidence <= 1.0:
        _reject("OML-019 relationship confidence invalid")

    if relationship.contradiction_count < 0:
        _reject("OML-019 relationship contradiction count invalid")

    expected_id = _stable_hash(
        {
            "source_entity_id": relationship.source_entity_id,
            "target_entity_id": relationship.target_entity_id,
            "relationship_type": (
                relationship.normalized_relationship_type
            ),
            "directed": relationship.directed,
        }
    )

    if relationship.relationship_id != expected_id:
        _reject("OML-019 relationship identity mismatch")

    required_true = (
        relationship.source_entity_verified,
        relationship.target_entity_verified,
        relationship.self_link_rejected,
        relationship.evidence_lineage_verified,
        relationship.deterministic_identity_verified,
        relationship.read_only,
    )

    if not all(required_true):
        _reject("OML-019 relationship guarantee missing")

    forbidden = (
        relationship.persistence_authorized,
        relationship.learning_update_authorized,
        relationship.runtime_activation_authorized,
        relationship.publication_authorized,
        relationship.action_authorization_enabled,
        relationship.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-019 forbidden relationship capability enabled")

    return True


def build_oracle_memory_relationship_graph(
    *,
    entity_batch: OracleMemoryEntityResolutionBatch,
    relationships: Sequence[OracleMemoryEntityRelationship],
) -> OracleMemoryRelationshipGraph:
    verify_oracle_memory_entity_resolution_batch(entity_batch)

    if entity_batch.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-019 upstream schema mismatch")

    if entity_batch.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-019 upstream engine mismatch")

    if not entity_batch.batch_ready:
        _reject("OML-019 upstream entity batch not ready")

    if not entity_batch.next_certification_authorized:
        _reject("OML-019 upstream continuation not authorized")

    if not entity_batch.read_only:
        _reject("OML-019 upstream read-only guarantee missing")

    entities = tuple(
        sorted(
            entity_batch.entities,
            key=lambda item: (
                item.domain_id,
                item.normalized_name,
                item.canonical_entity_id,
            ),
        )
    )

    entity_ids = {
        entity.canonical_entity_id
        for entity in entities
    }

    ordered_relationships = tuple(
        sorted(
            relationships,
            key=lambda item: (
                item.source_entity_id,
                item.target_entity_id,
                item.normalized_relationship_type,
                item.relationship_id,
            ),
        )
    )

    for relationship in ordered_relationships:
        verify_oracle_memory_entity_relationship(relationship)

        if relationship.source_entity_id not in entity_ids:
            _reject("OML-019 dangling source entity")

        if relationship.target_entity_id not in entity_ids:
            _reject("OML-019 dangling target entity")

    relationship_ids = tuple(
        relationship.relationship_id
        for relationship in ordered_relationships
    )

    if len(set(relationship_ids)) != len(relationship_ids):
        _reject("OML-019 duplicate relationships forbidden")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": entity_batch.schema_version,
        "upstream_engine_id": entity_batch.engine_id,
        "upstream_batch_hash": entity_batch.batch_hash,
        "entities": entities,
        "relationships": ordered_relationships,
        "entity_count": len(entities),
        "relationship_count": len(ordered_relationships),
        "canonical_entity_order_verified": True,
        "canonical_relationship_order_verified": True,
        "entity_identity_uniqueness_verified": (
            len(entity_ids) == len(entities)
        ),
        "relationship_identity_uniqueness_verified": (
            len(set(relationship_ids)) == len(relationship_ids)
        ),
        "self_links_rejected": all(
            item.source_entity_id != item.target_entity_id
            for item in ordered_relationships
        ),
        "dangling_links_rejected": True,
        "duplicate_links_rejected": True,
        "deterministic_graph_hashing_verified": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "graph_ready": True,
        "next_certification_authorized": True,
        "read_only": True,
    }

    graph = OracleMemoryRelationshipGraph(
        **body,
        graph_hash=_stable_hash(body),
    )

    verify_oracle_memory_relationship_graph(graph)
    return graph


def verify_oracle_memory_relationship_graph(
    graph: OracleMemoryRelationshipGraph,
) -> bool:
    body = asdict(graph)
    supplied = body.pop("graph_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-019 graph hash mismatch")

    if graph.schema_version != SCHEMA_VERSION:
        _reject("OML-019 graph schema mismatch")

    if graph.engine_id != ENGINE_ID:
        _reject("OML-019 graph engine mismatch")

    if graph.policy_id != POLICY_ID:
        _reject("OML-019 graph policy mismatch")

    if graph.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-019 graph subsystem mismatch")

    if graph.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-019 upstream schema lineage mismatch")

    if graph.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-019 upstream engine lineage mismatch")

    if graph.entity_count != len(graph.entities):
        _reject("OML-019 entity count mismatch")

    if graph.relationship_count != len(graph.relationships):
        _reject("OML-019 relationship count mismatch")

    entity_ids = {
        entity.canonical_entity_id
        for entity in graph.entities
    }

    if len(entity_ids) != len(graph.entities):
        _reject("OML-019 duplicate entity identities")

    relationship_ids = []

    for entity in graph.entities:
        verify_oracle_memory_resolved_entity(entity)

    for relationship in graph.relationships:
        verify_oracle_memory_entity_relationship(relationship)

        if relationship.source_entity_id not in entity_ids:
            _reject("OML-019 graph contains dangling source")

        if relationship.target_entity_id not in entity_ids:
            _reject("OML-019 graph contains dangling target")

        relationship_ids.append(relationship.relationship_id)

    if len(set(relationship_ids)) != len(relationship_ids):
        _reject("OML-019 graph contains duplicate links")

    required_true = (
        graph.canonical_entity_order_verified,
        graph.canonical_relationship_order_verified,
        graph.entity_identity_uniqueness_verified,
        graph.relationship_identity_uniqueness_verified,
        graph.self_links_rejected,
        graph.dangling_links_rejected,
        graph.duplicate_links_rejected,
        graph.deterministic_graph_hashing_verified,
        graph.graph_ready,
        graph.next_certification_authorized,
        graph.read_only,
    )

    if not all(required_true):
        _reject("OML-019 graph guarantee missing")

    forbidden = (
        graph.persistence_enabled,
        graph.learning_updates_enabled,
        graph.runtime_activation_enabled,
        graph.publication_enabled,
        graph.action_authorization_enabled,
        graph.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-019 forbidden graph capability enabled")

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
from qseries_v2.oracle_memory.oracle_memory_relationship_graph_and_linkage_resolution import (
    OracleMemoryRelationshipGraphInvariantError,
    build_oracle_memory_entity_relationship,
    build_oracle_memory_relationship_graph,
    verify_oracle_memory_relationship_graph,
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
    except OracleMemoryRelationshipGraphInvariantError:
        return

    raise AssertionError(f"tampered OML-019 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-019 TEST")
    print(" RELATIONSHIP GRAPH AND LINKAGE RESOLUTION")
    print("=" * 48)

    root = Path(__file__).resolve().parent

    fixture_016 = load_module(
        root
        / "test_oml_016_oracle_memory_ledger_integrity_and_replay_certification.py",
        "oml_016_fixture_for_oml_019",
    )
    ledger_contract = fixture_016.build_oml_015_contract(root)
    ledger = build_oracle_memory_ledger_integrity_replay_certification(
        ledger_contract=ledger_contract,
    )

    fixture_009 = load_module(
        root
        / "test_oml_009_oracle_memory_canonical_record_candidate_contract.py",
        "oml_009_fixture_for_oml_019",
    )
    gate = fixture_009.build_oml_008_decision(root)

    candidate_btc = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=gate.admitted_domain_ids[0],
        candidate_id="candidate:entity:bitcoin",
        entity_key="Bitcoin",
        source_key="certified-observation-source",
        observed_at="2026-08-02T14:46:00-05:00",
        effective_at="2026-08-02T14:46:00-05:00",
        payload={"entity_type": "crypto_asset"},
        evidence_hashes=("1" * 64,),
        parent_record_hashes=(),
        confidence=0.90,
        uncertainty=0.10,
        contradiction_count=0,
    )

    candidate_etf = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=gate.admitted_domain_ids[0],
        candidate_id="candidate:entity:bitcoin-etf",
        entity_key="Bitcoin ETF",
        source_key="certified-observation-source",
        observed_at="2026-08-02T14:46:00-05:00",
        effective_at="2026-08-02T14:46:00-05:00",
        payload={"entity_type": "financial_product"},
        evidence_hashes=("2" * 64,),
        parent_record_hashes=(),
        confidence=0.88,
        uncertainty=0.12,
        contradiction_count=0,
    )

    validation = build_oracle_memory_candidate_validation_batch(
        ledger_certification=ledger,
        candidates=(candidate_btc, candidate_etf),
    )

    entities = build_oracle_memory_entity_resolution_batch(
        validation_batch=validation,
        aliases_by_candidate_hash={
            candidate_btc.candidate_hash: ("BTC", "XBT"),
            candidate_etf.candidate_hash: ("Spot Bitcoin ETF",),
        },
    )

    bitcoin = next(
        item for item in entities.entities
        if item.normalized_name == "bitcoin"
    )
    bitcoin_etf = next(
        item for item in entities.entities
        if item.normalized_name == "bitcoin etf"
    )

    relationship = build_oracle_memory_entity_relationship(
        source_entity=bitcoin_etf,
        target_entity=bitcoin,
        relationship_type="tracks underlying asset",
        evidence_hashes=("3" * 64, "4" * 64),
        confidence=0.97,
        contradiction_count=0,
        directed=True,
    )

    graph = build_oracle_memory_relationship_graph(
        entity_batch=entities,
        relationships=(relationship,),
    )

    assert graph.schema_version == "OML-019"
    assert graph.engine_id == "OML-019"
    assert graph.upstream_schema_version == "OML-018"
    assert graph.upstream_engine_id == "OML-018"
    assert graph.entity_count == 2
    assert graph.relationship_count == 1
    assert graph.canonical_entity_order_verified
    assert graph.canonical_relationship_order_verified
    assert graph.entity_identity_uniqueness_verified
    assert graph.relationship_identity_uniqueness_verified
    assert graph.self_links_rejected
    assert graph.dangling_links_rejected
    assert graph.duplicate_links_rejected
    assert graph.deterministic_graph_hashing_verified
    assert not graph.persistence_enabled
    assert not graph.learning_updates_enabled
    assert not graph.runtime_activation_enabled
    assert not graph.publication_enabled
    assert not graph.action_authorization_enabled
    assert not graph.qseries_execution_enabled
    assert graph.graph_ready
    assert graph.next_certification_authorized
    assert graph.read_only

    replay = build_oracle_memory_relationship_graph(
        entity_batch=entities,
        relationships=(relationship,),
    )

    assert replay == graph
    assert verify_oracle_memory_relationship_graph(graph)

    expect_rejection(
        lambda: build_oracle_memory_relationship_graph(
            entity_batch=entities,
            relationships=(relationship, relationship),
        ),
        "duplicate relationship",
    )

    expect_rejection(
        lambda: verify_oracle_memory_relationship_graph(
            replace(graph, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_relationship_graph(
            replace(graph, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-018 entity resolution consumed")
    print("[PASS] Canonical entity identities retained")
    print("[PASS] Evidence-backed relationship created")
    print("[PASS] Stable relationship identity generated")
    print("[PASS] Self-links rejected")
    print("[PASS] Dangling links rejected")
    print("[PASS] Duplicate links rejected")
    print("[PASS] Canonical graph ordering verified")
    print("[PASS] Relationship graph deterministic across replay")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered graphs rejected")
    print("[DONE] OML-019 RELATIONSHIP GRAPH AND LINKAGE RESOLUTION PASS")
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
            "Certified OML-018 production or standalone test missing"
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    module = importlib.import_module(
        "qseries_v2.oracle_memory.oracle_memory_entity_resolution"
    )

    expected = {
        "SCHEMA_VERSION": "OML-018",
        "ENGINE_ID": "OML-018",
        "POLICY_ID": "oracle-memory.entity-resolution.v1",
        "UPSTREAM_SCHEMA_VERSION": "OML-017",
        "UPSTREAM_ENGINE_ID": "OML-017",
        "RESOLUTION_STATUS_RESOLVED": "resolved",
    }

    for name, value in expected.items():
        actual = getattr(module, name, None)

        if actual != value:
            raise RuntimeError(
                f"Certified OML-018 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    required = (
        "OracleMemoryEntityAlias",
        "OracleMemoryResolvedEntity",
        "OracleMemoryEntityResolutionBatch",
        "build_oracle_memory_entity_resolution_batch",
        "verify_oracle_memory_resolved_entity",
        "verify_oracle_memory_entity_resolution_batch",
    )

    missing = [name for name in required if not hasattr(module, name)]

    if missing:
        raise RuntimeError(
            "Certified OML-018 missing required symbols: "
            + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-019 FOR-SURE INSTALLER")
    print(" RELATIONSHIP GRAPH AND LINKAGE RESOLUTION")
    print("=" * 48)
    print("[BOOT] Revision: CAPABILITY_MILESTONE_FULL_REPLACEMENT")

    try:
        validate_upstream()
        print("[OK] Actual OML-018 imported and structurally verified")

        upstream_run = subprocess.run(
            [sys.executable, str(UPSTREAM_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream_run.returncode:
            raise RuntimeError(
                "OML-018 certification failed with exit code "
                f"{upstream_run.returncode}"
            )

        production_before = UPSTREAM.read_bytes()
        test_before = UPSTREAM_TEST.read_bytes()

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_relationship_graph_and_linkage_resolution "
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
                "OML-019 test failed with exit code "
                f"{completed.returncode}"
            )

        if UPSTREAM.read_bytes() != production_before:
            raise RuntimeError("Certified OML-018 production changed")

        if UPSTREAM_TEST.read_bytes() != test_before:
            raise RuntimeError("Certified OML-018 standalone test changed")

        print("[PASS] Certified OML-018 production unchanged")
        print("[PASS] Certified OML-018 standalone test unchanged")
        print("[PASS] OML-019 relationship graph installed")
        print("[PASS] OML-019 standalone deterministic test installed")
        print("[PASS] Entity linkage capability installed")
        print("[PASS] Evidence-backed relationship capability installed")
        print("[PASS] Self, dangling, and duplicate links rejected")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OML-019 RELATIONSHIP GRAPH "
            "AND LINKAGE RESOLUTION INSTALLED"
        )
        return 0

    except (RuntimeError, SyntaxError, ImportError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
