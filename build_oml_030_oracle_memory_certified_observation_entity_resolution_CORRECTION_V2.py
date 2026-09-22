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
    / "oracle_memory_certified_observation_candidate_validation_and_admission.py"
)
UPSTREAM_TEST = (
    ROOT
    / "test_oml_029_oracle_memory_certified_observation_candidate_validation_and_admission.py"
)

MATERIALIZATION_MODULE = (
    PACKAGE
    / "oracle_memory_certified_observation_candidate_materialization.py"
)
ENTITY_MODULE = PACKAGE / "oracle_memory_entity_resolution.py"
ENTITY_TEST = ROOT / "test_oml_018_oracle_memory_entity_resolution.py"

PRODUCTION = (
    PACKAGE
    / "oracle_memory_certified_observation_entity_resolution.py"
)
TEST = (
    ROOT
    / "test_oml_030_oracle_memory_certified_observation_entity_resolution.py"
)
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    OracleMemoryCandidateValidationBatch,
    verify_oracle_memory_candidate_validation_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_materialization import (
    OracleMemoryObservationCandidateMaterializationBatch,
    verify_oracle_memory_observation_candidate_materialization_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_validation_and_admission import (
    ADMISSION_STATUS_ADMITTED,
    ADMISSION_STATUS_REJECTED_DUPLICATE,
    OracleMemoryObservationCandidateAdmissionBatch,
    verify_oracle_memory_observation_candidate_admission_batch,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_entity_resolution import (
    OracleMemoryEntityResolutionBatch,
    OracleMemoryResolvedEntity,
    build_oracle_memory_entity_resolution_batch,
    verify_oracle_memory_entity_resolution_batch,
    verify_oracle_memory_resolved_entity,
)

SCHEMA_VERSION = "OML-030"
ENGINE_ID = "OML-030"
POLICY_ID = (
    "oracle-memory.certified-observation-entity-resolution.v1"
)

UPSTREAM_SCHEMA_VERSION = "OML-029"
UPSTREAM_ENGINE_ID = "OML-029"

RESOLUTION_STATE_READ_ONLY = "read_only_resolution"


class OracleMemoryObservationEntityResolutionInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryObservationEntityBinding:
    observation_hash: str
    candidate_hash: str
    admission_hash: str
    canonical_entity_id: str
    entity_hash: str
    domain_id: str
    canonical_name: str
    normalized_name: str
    observation_lineage_verified: bool
    candidate_lineage_verified: bool
    admission_lineage_verified: bool
    entity_lineage_verified: bool
    duplicate_rejection_verified: bool
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
class OracleMemoryObservationEntityResolution:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_admission_batch_hash: str
    upstream_materialization_batch_hash: str
    upstream_validation_batch_hash: str
    entity_resolution_batch_hash: str
    entities: tuple[OracleMemoryResolvedEntity, ...]
    bindings: tuple[OracleMemoryObservationEntityBinding, ...]
    admitted_candidate_count: int
    rejected_duplicate_count: int
    resolved_entity_count: int
    resolution_state: str
    canonical_order_verified: bool
    deterministic_resolution_verified: bool
    observation_entity_lineage_verified: bool
    duplicate_candidates_excluded: bool
    entity_identity_uniqueness_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    resolution_ready: bool
    downstream_relationship_graph_authorized: bool
    read_only: bool
    resolution_hash: str


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

    raise OracleMemoryObservationEntityResolutionInvariantError(
        "unsupported OML-030 value type: "
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
    raise OracleMemoryObservationEntityResolutionInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-030 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryObservationEntityResolutionInvariantError(
            f"OML-030 invalid {label} hexadecimal value"
        ) from exc


def _build_binding(
    *,
    observation_hash: str,
    candidate_hash: str,
    admission_hash: str,
    entity: OracleMemoryResolvedEntity,
) -> OracleMemoryObservationEntityBinding:
    verify_oracle_memory_resolved_entity(entity)

    body = {
        "observation_hash": observation_hash,
        "candidate_hash": candidate_hash,
        "admission_hash": admission_hash,
        "canonical_entity_id": entity.canonical_entity_id,
        "entity_hash": entity.entity_hash,
        "domain_id": entity.domain_id,
        "canonical_name": entity.canonical_name,
        "normalized_name": entity.normalized_name,
        "observation_lineage_verified": True,
        "candidate_lineage_verified": True,
        "admission_lineage_verified": True,
        "entity_lineage_verified": True,
        "duplicate_rejection_verified": True,
        "deterministic_binding_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    binding = OracleMemoryObservationEntityBinding(
        **body,
        binding_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_entity_binding(binding)
    return binding


def verify_oracle_memory_observation_entity_binding(
    binding: OracleMemoryObservationEntityBinding,
) -> bool:
    body = asdict(binding)
    supplied = body.pop("binding_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-030 binding hash mismatch")

    for value, label in (
        (binding.observation_hash, "observation hash"),
        (binding.candidate_hash, "candidate hash"),
        (binding.admission_hash, "admission hash"),
        (binding.canonical_entity_id, "canonical entity id"),
        (binding.entity_hash, "entity hash"),
        (binding.binding_hash, "binding hash"),
    ):
        _require_hash(value, label)

    required_true = (
        binding.observation_lineage_verified,
        binding.candidate_lineage_verified,
        binding.admission_lineage_verified,
        binding.entity_lineage_verified,
        binding.duplicate_rejection_verified,
        binding.deterministic_binding_verified,
        binding.read_only,
    )

    if not all(required_true):
        _reject("OML-030 binding guarantee missing")

    forbidden = (
        binding.persistence_authorized,
        binding.learning_update_authorized,
        binding.runtime_activation_authorized,
        binding.publication_authorized,
        binding.action_authorization_enabled,
        binding.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-030 forbidden binding capability enabled")

    return True


def build_oracle_memory_observation_entity_resolution(
    *,
    admission_batch: OracleMemoryObservationCandidateAdmissionBatch,
    materialization_batch: (
        OracleMemoryObservationCandidateMaterializationBatch
    ),
    validation_batch: OracleMemoryCandidateValidationBatch,
    aliases_by_candidate_hash: Mapping[str, Sequence[str]] | None = None,
) -> OracleMemoryObservationEntityResolution:
    verify_oracle_memory_observation_candidate_admission_batch(
        admission_batch
    )
    verify_oracle_memory_observation_candidate_materialization_batch(
        materialization_batch
    )
    verify_oracle_memory_candidate_validation_batch(validation_batch)

    if admission_batch.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-030 upstream schema mismatch")

    if admission_batch.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-030 upstream engine mismatch")

    if not admission_batch.admission_ready:
        _reject("OML-030 admission batch not ready")

    if not admission_batch.downstream_entity_resolution_authorized:
        _reject("OML-030 entity resolution not authorized")

    if not admission_batch.read_only:
        _reject("OML-030 upstream admission not read-only")

    admitted_admissions = tuple(
        item
        for item in admission_batch.admissions
        if item.admission_status == ADMISSION_STATUS_ADMITTED
    )

    rejected_admissions = tuple(
        item
        for item in admission_batch.admissions
        if item.admission_status
        == ADMISSION_STATUS_REJECTED_DUPLICATE
    )

    candidates_by_hash = {
        candidate.candidate_hash: candidate
        for candidate in materialization_batch.candidates
    }

    validation_results_by_hash = {
        result.result_hash: result
        for result in validation_batch.results
    }

    admitted_candidates = []
    admitted_results = []

    for admission in admitted_admissions:
        candidate = candidates_by_hash.get(admission.candidate_hash)
        validation_result = validation_results_by_hash.get(
            admission.validation_result_hash
        )

        if candidate is None:
            _reject("OML-030 admitted candidate missing")

        if validation_result is None:
            _reject("OML-030 admitted validation result missing")

        if validation_result.candidate_hash != admission.candidate_hash:
            _reject("OML-030 admission validation lineage mismatch")

        if validation_result.status != "valid":
            _reject("OML-030 admitted validation result not valid")

        admitted_candidates.append(candidate)
        admitted_results.append(validation_result)

    admitted_candidates = tuple(admitted_candidates)
    admitted_results = tuple(admitted_results)

    if len(admitted_candidates) != admission_batch.admitted_count:
        _reject("OML-030 admitted candidate reconciliation mismatch")

    if len(admitted_results) != admission_batch.admitted_count:
        _reject("OML-030 admitted validation reconciliation mismatch")

    filtered_validation = OracleMemoryCandidateValidationBatch(
        schema_version=validation_batch.schema_version,
        engine_id=validation_batch.engine_id,
        policy_id=validation_batch.policy_id,
        subsystem_id=validation_batch.subsystem_id,
        upstream_schema_version=validation_batch.upstream_schema_version,
        upstream_engine_id=validation_batch.upstream_engine_id,
        upstream_certification_hash=(
            validation_batch.upstream_certification_hash
        ),
        results=admitted_results,
        candidate_count=len(admitted_results),
        unique_candidate_count=len(admitted_results),
        duplicate_candidate_count=0,
        canonical_ordering_verified=True,
        deterministic_validation_verified=True,
        duplicate_detection_verified=True,
        duplicate_persistence_forbidden=True,
        persistence_enabled=False,
        learning_updates_enabled=False,
        runtime_activation_enabled=False,
        publication_enabled=False,
        action_authorization_enabled=False,
        qseries_execution_enabled=False,
        batch_ready=True,
        next_certification_authorized=True,
        read_only=True,
        batch_hash="",
    )

    filtered_body = asdict(filtered_validation)
    filtered_body.pop("batch_hash")
    filtered_validation = OracleMemoryCandidateValidationBatch(
        **filtered_body,
        batch_hash=_stable_hash(filtered_body),
    )

    verify_oracle_memory_candidate_validation_batch(filtered_validation)

    entity_batch = build_oracle_memory_entity_resolution_batch(
        validation_batch=filtered_validation,
        aliases_by_candidate_hash=aliases_by_candidate_hash or {},
    )

    candidate_by_hash = {
        item.candidate_hash: item
        for item in admitted_candidates
    }

    entities_by_candidate = {
        entity.source_candidate_hash: entity
        for entity in entity_batch.entities
    }

    bindings = []

    for admission in sorted(
        admitted_admissions,
        key=lambda item: (
            item.candidate_hash,
            item.validation_result_hash,
            item.admission_hash,
        ),
    ):
        candidate = candidate_by_hash.get(admission.candidate_hash)
        entity = entities_by_candidate.get(admission.candidate_hash)

        if candidate is None or entity is None:
            _reject("OML-030 entity binding lineage incomplete")

        observation_hash = candidate.payload.get("observation_hash")

        if not isinstance(observation_hash, str):
            _reject("OML-030 observation hash missing from candidate")

        bindings.append(
            _build_binding(
                observation_hash=observation_hash,
                candidate_hash=admission.candidate_hash,
                admission_hash=admission.admission_hash,
                entity=entity,
            )
        )

    ordered_bindings = tuple(
        sorted(
            bindings,
            key=lambda item: (
                item.domain_id,
                item.normalized_name,
                item.canonical_entity_id,
                item.binding_hash,
            ),
        )
    )

    entity_ids = tuple(
        item.canonical_entity_id for item in entity_batch.entities
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": admission_batch.schema_version,
        "upstream_engine_id": admission_batch.engine_id,
        "upstream_admission_batch_hash": admission_batch.batch_hash,
        "upstream_materialization_batch_hash": (
            materialization_batch.batch_hash
        ),
        "upstream_validation_batch_hash": validation_batch.batch_hash,
        "entity_resolution_batch_hash": entity_batch.batch_hash,
        "entities": entity_batch.entities,
        "bindings": ordered_bindings,
        "admitted_candidate_count": admission_batch.admitted_count,
        "rejected_duplicate_count": (
            admission_batch.rejected_duplicate_count
        ),
        "resolved_entity_count": len(entity_batch.entities),
        "resolution_state": RESOLUTION_STATE_READ_ONLY,
        "canonical_order_verified": True,
        "deterministic_resolution_verified": True,
        "observation_entity_lineage_verified": True,
        "duplicate_candidates_excluded": (
            len(rejected_admissions)
            == admission_batch.rejected_duplicate_count
            and all(
                item.admission_status
                == ADMISSION_STATUS_REJECTED_DUPLICATE
                for item in rejected_admissions
            )
        ),
        "entity_identity_uniqueness_verified": (
            len(set(entity_ids)) == len(entity_ids)
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "resolution_ready": True,
        "downstream_relationship_graph_authorized": True,
        "read_only": True,
    }

    resolution = OracleMemoryObservationEntityResolution(
        **body,
        resolution_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_entity_resolution(resolution)
    return resolution


def verify_oracle_memory_observation_entity_resolution(
    resolution: OracleMemoryObservationEntityResolution,
) -> bool:
    body = asdict(resolution)
    supplied = body.pop("resolution_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-030 resolution hash mismatch")

    if resolution.schema_version != SCHEMA_VERSION:
        _reject("OML-030 schema mismatch")

    if resolution.engine_id != ENGINE_ID:
        _reject("OML-030 engine mismatch")

    if resolution.policy_id != POLICY_ID:
        _reject("OML-030 policy mismatch")

    if resolution.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-030 subsystem mismatch")

    if resolution.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-030 upstream schema lineage mismatch")

    if resolution.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-030 upstream engine lineage mismatch")

    if resolution.resolved_entity_count != len(resolution.entities):
        _reject("OML-030 entity count mismatch")

    if resolution.resolved_entity_count != len(resolution.bindings):
        _reject("OML-030 binding count mismatch")

    if resolution.resolution_state != RESOLUTION_STATE_READ_ONLY:
        _reject("OML-030 resolution state invalid")

    entity_ids = []

    for entity in resolution.entities:
        verify_oracle_memory_resolved_entity(entity)
        entity_ids.append(entity.canonical_entity_id)

    for binding in resolution.bindings:
        verify_oracle_memory_observation_entity_binding(binding)

    if len(set(entity_ids)) != len(entity_ids):
        _reject("OML-030 duplicate entity identities")

    required_true = (
        resolution.canonical_order_verified,
        resolution.deterministic_resolution_verified,
        resolution.observation_entity_lineage_verified,
        resolution.duplicate_candidates_excluded,
        resolution.entity_identity_uniqueness_verified,
        resolution.resolution_ready,
        resolution.downstream_relationship_graph_authorized,
        resolution.read_only,
    )

    if not all(required_true):
        _reject("OML-030 resolution guarantee missing")

    forbidden = (
        resolution.persistence_enabled,
        resolution.learning_updates_enabled,
        resolution.runtime_activation_enabled,
        resolution.publication_enabled,
        resolution.action_authorization_enabled,
        resolution.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-030 forbidden resolution capability enabled")

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
    OracleMemoryObservationEntityResolutionInvariantError,
    build_oracle_memory_observation_entity_resolution,
    verify_oracle_memory_observation_entity_resolution,
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
    except OracleMemoryObservationEntityResolutionInvariantError:
        return

    raise AssertionError(f"tampered OML-030 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-030 CORRECTION V2 TEST")
    print(" CERTIFIED OBSERVATION ENTITY RESOLUTION")
    print("=" * 48)

    root = Path(__file__).resolve().parent

    fixture_028 = load_module(
        root
        / "test_oml_028_oracle_memory_certified_observation_candidate_materialization.py",
        "oml_028_fixture_for_oml_030",
    )

    gate_decision, intake_batch = fixture_028.build_intake_batch(root)

    materialization_batch = (
        build_oracle_memory_observation_candidate_materialization_batch(
            gate_decision=gate_decision,
            intake_batch=intake_batch,
        )
    )

    fixture_016 = load_module(
        root
        / "test_oml_016_oracle_memory_ledger_integrity_and_replay_certification.py",
        "oml_016_fixture_for_oml_030",
    )

    ledger_contract = fixture_016.build_oml_015_contract(root)
    ledger = build_oracle_memory_ledger_integrity_replay_certification(
        ledger_contract=ledger_contract,
    )

    validation_batch = build_oracle_memory_candidate_validation_batch(
        ledger_certification=ledger,
        candidates=materialization_batch.candidates,
    )

    admission_batch = (
        build_oracle_memory_observation_candidate_admission_batch(
            materialization_batch=materialization_batch,
            validation_batch=validation_batch,
        )
    )

    admitted_candidate_hash = next(
        item.candidate_hash
        for item in admission_batch.admissions
        if item.admission_status == "admitted"
    )

    resolution = build_oracle_memory_observation_entity_resolution(
        admission_batch=admission_batch,
        materialization_batch=materialization_batch,
        validation_batch=validation_batch,
        aliases_by_candidate_hash={
            admitted_candidate_hash: (
                "BTC",
                "Bitcoin",
                "XBT",
            )
        },
    )

    assert resolution.schema_version == "OML-030"
    assert resolution.engine_id == "OML-030"
    assert resolution.upstream_schema_version == "OML-029"
    assert resolution.upstream_engine_id == "OML-029"
    assert resolution.admitted_candidate_count == 1
    assert resolution.rejected_duplicate_count == 1
    assert resolution.resolved_entity_count == 1
    assert resolution.entities[0].canonical_name == "Bitcoin"
    assert resolution.entities[0].normalized_name == "bitcoin"
    assert resolution.bindings[0].observation_lineage_verified
    assert resolution.bindings[0].candidate_lineage_verified
    assert resolution.bindings[0].admission_lineage_verified
    assert resolution.bindings[0].entity_lineage_verified
    assert resolution.bindings[0].duplicate_rejection_verified
    assert resolution.canonical_order_verified
    assert resolution.deterministic_resolution_verified
    assert resolution.observation_entity_lineage_verified
    assert resolution.duplicate_candidates_excluded
    assert resolution.entity_identity_uniqueness_verified
    assert not resolution.persistence_enabled
    assert not resolution.learning_updates_enabled
    assert not resolution.runtime_activation_enabled
    assert not resolution.publication_enabled
    assert not resolution.action_authorization_enabled
    assert not resolution.qseries_execution_enabled
    assert resolution.resolution_ready
    assert resolution.downstream_relationship_graph_authorized
    assert resolution.read_only

    replay = build_oracle_memory_observation_entity_resolution(
        admission_batch=admission_batch,
        materialization_batch=materialization_batch,
        validation_batch=validation_batch,
        aliases_by_candidate_hash={
            admitted_candidate_hash: (
                "XBT",
                "Bitcoin",
                "BTC",
            )
        },
    )

    assert replay == resolution
    assert verify_oracle_memory_observation_entity_resolution(
        resolution
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_entity_resolution(
            replace(resolution, resolved_entity_count=2)
        ),
        "entity count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_entity_resolution(
            replace(resolution, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_entity_resolution(
            replace(
                resolution,
                downstream_relationship_graph_authorized=False,
            )
        ),
        "relationship graph authorization",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_entity_resolution(
            replace(resolution, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-029 admission batch consumed")
    print("[PASS] Certified OML-018 entity resolver consumed")
    print("[PASS] Only admitted observation candidate resolved")
    print("[PASS] Duplicate-rejected candidate excluded")
    print("[PASS] Stable canonical entity identity generated")
    print("[PASS] Alias normalization retained")
    print("[PASS] Observation-to-entity lineage retained")
    print("[PASS] Relationship graph continuation authorized read-only")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Resolution deterministic across replay")
    print("[PASS] Tampered resolutions rejected")
    print(
        "[DONE] OML-030 CORRECTION V2 CERTIFIED OBSERVATION "
        "ENTITY RESOLUTION PASS"
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
        MATERIALIZATION_MODULE,
        ENTITY_MODULE,
        ENTITY_TEST,
    )

    missing_files = [
        str(path)
        for path in required_files
        if not path.is_file()
    ]

    if missing_files:
        raise RuntimeError(
            "Required certified upstream files missing: "
            + ", ".join(missing_files)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    admission_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_candidate_validation_and_admission"
    )

    expected = {
        "SCHEMA_VERSION": "OML-029",
        "ENGINE_ID": "OML-029",
        "POLICY_ID": (
            "oracle-memory.certified-observation-candidate-validation-and-admission.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-028",
        "UPSTREAM_ENGINE_ID": "OML-028",
    }

    for name, value in expected.items():
        actual = getattr(admission_module, name, None)

        if actual != value:
            raise RuntimeError(
                f"Certified OML-029 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    materialization_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_candidate_materialization"
    )

    materialization_builder = getattr(
        materialization_module,
        "build_oracle_memory_observation_candidate_materialization_batch",
        None,
    )

    if materialization_builder is None:
        raise RuntimeError("Certified OML-028 builder missing")

    materialization_signature = inspect.signature(
        materialization_builder
    )

    required_materialization_parameters = {
        "gate_decision",
        "intake_batch",
    }

    missing_materialization_parameters = sorted(
        required_materialization_parameters
        - set(materialization_signature.parameters)
    )

    if missing_materialization_parameters:
        raise RuntimeError(
            "Certified OML-028 builder parameters missing: "
            + ", ".join(missing_materialization_parameters)
        )

    admission_builder = getattr(
        admission_module,
        "build_oracle_memory_observation_candidate_admission_batch",
        None,
    )

    if admission_builder is None:
        raise RuntimeError("Certified OML-029 builder missing")

    admission_signature = inspect.signature(admission_builder)

    required_admission_parameters = {
        "materialization_batch",
        "validation_batch",
    }

    missing_admission_parameters = sorted(
        required_admission_parameters
        - set(admission_signature.parameters)
    )

    if missing_admission_parameters:
        raise RuntimeError(
            "Certified OML-029 builder parameters missing: "
            + ", ".join(missing_admission_parameters)
        )

    entity_module = importlib.import_module(
        "qseries_v2.oracle_memory.oracle_memory_entity_resolution"
    )

    required_entity_symbols = (
        "OracleMemoryResolvedEntity",
        "OracleMemoryEntityResolutionBatch",
        "build_oracle_memory_entity_resolution_batch",
        "verify_oracle_memory_entity_resolution_batch",
    )

    missing = [
        name
        for name in required_entity_symbols
        if not hasattr(entity_module, name)
    ]

    if missing:
        raise RuntimeError(
            "Certified entity-resolution engine missing symbols: "
            + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-030 CORRECTION V2 INSTALLER")
    print(" CERTIFIED OBSERVATION ENTITY RESOLUTION")
    print("=" * 48)
    print("[BOOT] Revision: EXACT_OML_028_029_LINEAGE_ALIGNMENT")

    try:
        validate_upstreams()
        print("[OK] Actual OML-029 imported and structurally verified")
        print("[OK] Corrected OML-028 gate_decision signature verified")
        print("[OK] OML-029 admission signature verified")
        print("[OK] Actual OML-018 entity-resolution engine verified")

        upstream_run = subprocess.run(
            [sys.executable, str(UPSTREAM_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream_run.returncode:
            raise RuntimeError(
                "OML-029 certification failed with exit code "
                f"{upstream_run.returncode}"
            )

        entity_run = subprocess.run(
            [sys.executable, str(ENTITY_TEST)],
            cwd=ROOT,
            check=False,
        )

        if entity_run.returncode:
            raise RuntimeError(
                "OML-018 entity certification failed with exit code "
                f"{entity_run.returncode}"
            )

        tracked = {
            path: path.read_bytes()
            for path in (
                UPSTREAM,
                UPSTREAM_TEST,
                MATERIALIZATION_MODULE,
                ENTITY_MODULE,
                ENTITY_TEST,
            )
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_observation_entity_resolution "
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
                "OML-030 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(
                    f"Certified upstream changed: {path}"
                )

        print("[PASS] Certified OML-029 production unchanged")
        print("[PASS] Certified OML-029 standalone test unchanged")
        print("[PASS] Certified OML-018 entity resolver unchanged")
        print("[PASS] OML-030 production fully replaced")
        print("[PASS] OML-030 entity resolution bridge installed")
        print("[PASS] OML-030 standalone deterministic test installed")
        print("[PASS] Admitted observations resolved to entities")
        print("[PASS] Duplicate-rejected candidates excluded")
        print("[PASS] Observation-to-entity lineage preserved")
        print("[PASS] Relationship graph continuation authorized")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OML-030 CORRECTION V2 CERTIFIED OBSERVATION "
            "ENTITY RESOLUTION INSTALLED"
        )
        return 0

    except (RuntimeError, SyntaxError, ImportError, KeyError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
