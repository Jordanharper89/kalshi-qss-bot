from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_certified_observation_intake_contract.py"
UPSTREAM_TEST = (
    ROOT
    / "test_oml_027_oracle_memory_certified_observation_intake_contract.py"
)

CANDIDATE_MODULE = PACKAGE / "oracle_memory_canonical_record_candidate_contract.py"
CANDIDATE_TEST = (
    ROOT
    / "test_oml_009_oracle_memory_canonical_record_candidate_contract.py"
)

PRODUCTION = (
    PACKAGE
    / "oracle_memory_certified_observation_candidate_materialization.py"
)
TEST = (
    ROOT
    / "test_oml_028_oracle_memory_certified_observation_candidate_materialization.py"
)
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract import (
    OracleMemoryCanonicalRecordCandidate,
    verify_oracle_memory_canonical_record_candidate,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_intake_contract import (
    OracleMemoryCertifiedObservation,
    OracleMemoryObservationIntakeBatch,
    verify_oracle_memory_certified_observation,
    verify_oracle_memory_observation_intake_batch,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-028"
ENGINE_ID = "OML-028"
POLICY_ID = (
    "oracle-memory.certified-observation-candidate-materialization.v1"
)

UPSTREAM_SCHEMA_VERSION = "OML-027"
UPSTREAM_ENGINE_ID = "OML-027"

MATERIALIZATION_STATE_CONTRACT_ONLY = "contract_only"
MATERIALIZATION_STATUS_READY = "ready"
MATERIALIZATION_STATUS_DUPLICATE = "duplicate"


class OracleMemoryObservationMaterializationInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryObservationCandidateBinding:
    observation_hash: str
    observation_id: str
    candidate_hash: str
    candidate_id: str
    domain_id: str
    entity_key: str
    source_key: str
    materialization_status: str
    duplicate_of_candidate_hash: str | None
    observation_verified: bool
    candidate_verified: bool
    payload_lineage_verified: bool
    evidence_lineage_verified: bool
    parent_lineage_verified: bool
    source_certification_lineage_verified: bool
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
class OracleMemoryObservationCandidateMaterializationBatch:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_batch_hash: str
    candidates: tuple[OracleMemoryCanonicalRecordCandidate, ...]
    bindings: tuple[OracleMemoryObservationCandidateBinding, ...]
    observation_count: int
    candidate_count: int
    unique_candidate_count: int
    duplicate_candidate_count: int
    materialization_state: str
    canonical_order_verified: bool
    deterministic_materialization_verified: bool
    observation_candidate_lineage_verified: bool
    source_certification_lineage_verified: bool
    duplicate_detection_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    materialization_ready: bool
    downstream_validation_authorized: bool
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

    raise OracleMemoryObservationMaterializationInvariantError(
        "unsupported OML-028 value type: "
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
    raise OracleMemoryObservationMaterializationInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-028 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryObservationMaterializationInvariantError(
            f"OML-028 invalid {label} hexadecimal value"
        ) from exc


def _candidate_id_for(
    observation: OracleMemoryCertifiedObservation,
) -> str:
    return (
        "observation:"
        f"{observation.observation_kind}:"
        f"{observation.observation_id}"
    )


def _materialize_candidate(
    observation: OracleMemoryCertifiedObservation,
) -> OracleMemoryCanonicalRecordCandidate:
    verify_oracle_memory_certified_observation(observation)

    candidate_body = {
        "candidate_id": _candidate_id_for(observation),
        "domain_id": observation.domain_id,
        "entity_key": observation.entity_key,
        "source_key": observation.source_key,
        "observed_at": observation.observed_at,
        "effective_at": observation.effective_at,
        "payload": {
            "observation_id": observation.observation_id,
            "observation_hash": observation.observation_hash,
            "observation_kind": observation.observation_kind,
            "observation_payload": observation.payload,
            "source_certification_hash": (
                observation.source_certification_hash
            ),
        },
        "evidence_hashes": observation.evidence_hashes,
        "parent_record_hashes": (
            observation.parent_observation_hashes
        ),
        "confidence": observation.confidence,
        "uncertainty": observation.uncertainty,
        "contradiction_count": observation.contradiction_count,
        "candidate_state": "candidate_only",
        "persistent_storage_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    candidate = OracleMemoryCanonicalRecordCandidate(
        **candidate_body,
        candidate_hash=_stable_hash(candidate_body),
    )

    verify_oracle_memory_canonical_record_candidate(candidate)
    return candidate


def _build_binding(
    *,
    observation: OracleMemoryCertifiedObservation,
    candidate: OracleMemoryCanonicalRecordCandidate,
    duplicate_of_candidate_hash: str | None,
) -> OracleMemoryObservationCandidateBinding:
    verify_oracle_memory_certified_observation(observation)
    verify_oracle_memory_canonical_record_candidate(candidate)

    duplicate = duplicate_of_candidate_hash is not None

    body = {
        "observation_hash": observation.observation_hash,
        "observation_id": observation.observation_id,
        "candidate_hash": candidate.candidate_hash,
        "candidate_id": candidate.candidate_id,
        "domain_id": candidate.domain_id,
        "entity_key": candidate.entity_key,
        "source_key": candidate.source_key,
        "materialization_status": (
            MATERIALIZATION_STATUS_DUPLICATE
            if duplicate
            else MATERIALIZATION_STATUS_READY
        ),
        "duplicate_of_candidate_hash": duplicate_of_candidate_hash,
        "observation_verified": True,
        "candidate_verified": True,
        "payload_lineage_verified": (
            candidate.payload["observation_hash"]
            == observation.observation_hash
        ),
        "evidence_lineage_verified": (
            candidate.evidence_hashes == observation.evidence_hashes
        ),
        "parent_lineage_verified": (
            candidate.parent_record_hashes
            == observation.parent_observation_hashes
        ),
        "source_certification_lineage_verified": (
            candidate.payload["source_certification_hash"]
            == observation.source_certification_hash
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

    binding = OracleMemoryObservationCandidateBinding(
        **body,
        binding_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_candidate_binding(binding)
    return binding


def verify_oracle_memory_observation_candidate_binding(
    binding: OracleMemoryObservationCandidateBinding,
) -> bool:
    body = asdict(binding)
    supplied = body.pop("binding_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-028 binding hash mismatch")

    for value, label in (
        (binding.observation_hash, "observation hash"),
        (binding.observation_id, "observation id"),
        (binding.candidate_hash, "candidate hash"),
        (binding.binding_hash, "binding hash"),
    ):
        _require_hash(value, label)

    if binding.materialization_status not in (
        MATERIALIZATION_STATUS_READY,
        MATERIALIZATION_STATUS_DUPLICATE,
    ):
        _reject("OML-028 materialization status invalid")

    if binding.materialization_status == MATERIALIZATION_STATUS_DUPLICATE:
        if binding.duplicate_of_candidate_hash is None:
            _reject("OML-028 duplicate candidate lineage missing")
        _require_hash(
            binding.duplicate_of_candidate_hash,
            "duplicate candidate hash",
        )
    elif binding.duplicate_of_candidate_hash is not None:
        _reject("OML-028 unexpected duplicate lineage")

    required_true = (
        binding.observation_verified,
        binding.candidate_verified,
        binding.payload_lineage_verified,
        binding.evidence_lineage_verified,
        binding.parent_lineage_verified,
        binding.source_certification_lineage_verified,
        binding.deterministic_binding_verified,
        binding.read_only,
    )

    if not all(required_true):
        _reject("OML-028 binding guarantee missing")

    forbidden = (
        binding.persistence_authorized,
        binding.learning_update_authorized,
        binding.runtime_activation_authorized,
        binding.publication_authorized,
        binding.action_authorization_enabled,
        binding.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-028 forbidden binding capability enabled")

    return True


def build_oracle_memory_observation_candidate_materialization_batch(
    *,
    intake_batch: OracleMemoryObservationIntakeBatch,
) -> OracleMemoryObservationCandidateMaterializationBatch:
    verify_oracle_memory_observation_intake_batch(intake_batch)

    if intake_batch.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-028 upstream schema mismatch")

    if intake_batch.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-028 upstream engine mismatch")

    if not intake_batch.intake_ready:
        _reject("OML-028 upstream intake batch not ready")

    if not intake_batch.read_only:
        _reject("OML-028 upstream intake batch not read-only")

    ordered_observations = tuple(
        sorted(
            intake_batch.observations,
            key=lambda item: (
                item.domain_id,
                item.observed_at,
                item.entity_key,
                item.observation_id,
            ),
        )
    )

    candidates = tuple(
        _materialize_candidate(observation)
        for observation in ordered_observations
    )

    first_candidate_by_hash: dict[str, str] = {}
    bindings = []

    for observation, candidate in zip(
        ordered_observations,
        candidates,
        strict=True,
    ):
        duplicate_of = first_candidate_by_hash.get(
            candidate.candidate_hash
        )

        if duplicate_of is None:
            first_candidate_by_hash[
                candidate.candidate_hash
            ] = candidate.candidate_hash

        bindings.append(
            _build_binding(
                observation=observation,
                candidate=candidate,
                duplicate_of_candidate_hash=duplicate_of,
            )
        )

    binding_tuple = tuple(bindings)
    duplicate_count = sum(
        item.materialization_status
        == MATERIALIZATION_STATUS_DUPLICATE
        for item in binding_tuple
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": intake_batch.schema_version,
        "upstream_engine_id": intake_batch.engine_id,
        "upstream_batch_hash": intake_batch.batch_hash,
        "candidates": candidates,
        "bindings": binding_tuple,
        "observation_count": len(ordered_observations),
        "candidate_count": len(candidates),
        "unique_candidate_count": len(candidates) - duplicate_count,
        "duplicate_candidate_count": duplicate_count,
        "materialization_state": MATERIALIZATION_STATE_CONTRACT_ONLY,
        "canonical_order_verified": True,
        "deterministic_materialization_verified": True,
        "observation_candidate_lineage_verified": True,
        "source_certification_lineage_verified": True,
        "duplicate_detection_verified": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "materialization_ready": True,
        "downstream_validation_authorized": True,
        "read_only": True,
    }

    batch = OracleMemoryObservationCandidateMaterializationBatch(
        **body,
        batch_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_candidate_materialization_batch(
        batch
    )
    return batch


def verify_oracle_memory_observation_candidate_materialization_batch(
    batch: OracleMemoryObservationCandidateMaterializationBatch,
) -> bool:
    body = asdict(batch)
    supplied = body.pop("batch_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-028 batch hash mismatch")

    if batch.schema_version != SCHEMA_VERSION:
        _reject("OML-028 schema mismatch")

    if batch.engine_id != ENGINE_ID:
        _reject("OML-028 engine mismatch")

    if batch.policy_id != POLICY_ID:
        _reject("OML-028 policy mismatch")

    if batch.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-028 subsystem mismatch")

    if batch.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-028 upstream schema lineage mismatch")

    if batch.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-028 upstream engine lineage mismatch")

    if batch.observation_count != len(batch.bindings):
        _reject("OML-028 observation count mismatch")

    if batch.candidate_count != len(batch.candidates):
        _reject("OML-028 candidate count mismatch")

    if batch.candidate_count != batch.observation_count:
        _reject("OML-028 observation/candidate count mismatch")

    if (
        batch.unique_candidate_count
        + batch.duplicate_candidate_count
        != batch.candidate_count
    ):
        _reject("OML-028 duplicate count reconciliation mismatch")

    for candidate in batch.candidates:
        verify_oracle_memory_canonical_record_candidate(candidate)

    for binding in batch.bindings:
        verify_oracle_memory_observation_candidate_binding(binding)

    if batch.materialization_state != (
        MATERIALIZATION_STATE_CONTRACT_ONLY
    ):
        _reject("OML-028 materialization state invalid")

    required_true = (
        batch.canonical_order_verified,
        batch.deterministic_materialization_verified,
        batch.observation_candidate_lineage_verified,
        batch.source_certification_lineage_verified,
        batch.duplicate_detection_verified,
        batch.materialization_ready,
        batch.downstream_validation_authorized,
        batch.read_only,
    )

    if not all(required_true):
        _reject("OML-028 batch guarantee missing")

    forbidden = (
        batch.persistence_enabled,
        batch.learning_updates_enabled,
        batch.runtime_activation_enabled,
        batch.publication_enabled,
        batch.action_authorization_enabled,
        batch.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-028 forbidden batch capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_materialization import (
    MATERIALIZATION_STATUS_DUPLICATE,
    MATERIALIZATION_STATUS_READY,
    OracleMemoryObservationMaterializationInvariantError,
    build_oracle_memory_observation_candidate_materialization_batch,
    verify_oracle_memory_observation_candidate_materialization_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_intake_contract import (
    OBSERVATION_KIND_REAL_WORLD,
    build_oracle_memory_certified_observation,
    build_oracle_memory_observation_intake_batch,
)
from qseries_v2.oracle_memory.oracle_memory_cross_market_dependency_memory import (
    build_oracle_memory_cross_market_dependency_memory,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
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
    except OracleMemoryObservationMaterializationInvariantError:
        return

    raise AssertionError(f"tampered OML-028 {label} accepted")


def build_intake_batch(root: Path):
    fixture = load_module(
        root / "test_oml_026_oracle_memory_cross_market_dependency_memory.py",
        "oml_026_fixture_for_oml_028",
    )

    chain_memory, _ = fixture.build_chain_memory(root)

    cross_market_memory = build_oracle_memory_cross_market_dependency_memory(
        causal_chain_memory=chain_memory,
        dependencies=(),
    )

    observation = build_oracle_memory_certified_observation(
        observation_kind=OBSERVATION_KIND_REAL_WORLD,
        domain_id=MEMORY_DOMAINS[0],
        entity_key="Bitcoin",
        source_key="oracle-live-shadow",
        observed_at="2026-08-02T15:00:00-05:00",
        effective_at="2026-08-02T15:00:00-05:00",
        payload={
            "observation": (
                "Stablecoin liquidity increased before Bitcoin "
                "market repricing."
            ),
            "observation_type": "liquidity_shift",
            "market": "bitcoin",
        },
        evidence_hashes=("1" * 64, "2" * 64),
        source_certification_hash="3" * 64,
        confidence=0.81,
        uncertainty=0.19,
        contradiction_count=0,
    )

    return build_oracle_memory_observation_intake_batch(
        cross_market_memory=cross_market_memory,
        observations=(observation, observation),
    )


def main() -> int:
    print("=" * 48)
    print(" OML-028 TEST")
    print(" CERTIFIED OBSERVATION CANDIDATE MATERIALIZATION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    intake_batch = build_intake_batch(root)

    batch = (
        build_oracle_memory_observation_candidate_materialization_batch(
            intake_batch=intake_batch,
        )
    )

    assert batch.schema_version == "OML-028"
    assert batch.engine_id == "OML-028"
    assert batch.upstream_schema_version == "OML-027"
    assert batch.upstream_engine_id == "OML-027"
    assert batch.observation_count == 2
    assert batch.candidate_count == 2
    assert batch.unique_candidate_count == 1
    assert batch.duplicate_candidate_count == 1
    assert batch.bindings[0].materialization_status == (
        MATERIALIZATION_STATUS_READY
    )
    assert batch.bindings[1].materialization_status == (
        MATERIALIZATION_STATUS_DUPLICATE
    )
    assert (
        batch.bindings[1].duplicate_of_candidate_hash
        == batch.candidates[0].candidate_hash
    )
    assert batch.canonical_order_verified
    assert batch.deterministic_materialization_verified
    assert batch.observation_candidate_lineage_verified
    assert batch.source_certification_lineage_verified
    assert batch.duplicate_detection_verified
    assert not batch.persistence_enabled
    assert not batch.learning_updates_enabled
    assert not batch.runtime_activation_enabled
    assert not batch.publication_enabled
    assert not batch.action_authorization_enabled
    assert not batch.qseries_execution_enabled
    assert batch.materialization_ready
    assert batch.downstream_validation_authorized
    assert batch.read_only

    candidate = batch.candidates[0]
    binding = batch.bindings[0]

    assert candidate.payload["observation_hash"] == (
        binding.observation_hash
    )
    assert candidate.evidence_hashes == (
        intake_batch.observations[0].evidence_hashes
    )
    assert candidate.parent_record_hashes == (
        intake_batch.observations[0].parent_observation_hashes
    )
    assert candidate.payload["source_certification_hash"] == (
        intake_batch.observations[0].source_certification_hash
    )

    replay = (
        build_oracle_memory_observation_candidate_materialization_batch(
            intake_batch=intake_batch,
        )
    )

    assert replay == batch
    assert (
        verify_oracle_memory_observation_candidate_materialization_batch(
            batch
        )
    )

    expect_rejection(
        lambda: (
            verify_oracle_memory_observation_candidate_materialization_batch(
                replace(batch, candidate_count=3)
            )
        ),
        "candidate count",
    )

    expect_rejection(
        lambda: (
            verify_oracle_memory_observation_candidate_materialization_batch(
                replace(batch, persistence_enabled=True)
            )
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: (
            verify_oracle_memory_observation_candidate_materialization_batch(
                replace(batch, downstream_validation_authorized=False)
            )
        ),
        "downstream validation authorization",
    )

    expect_rejection(
        lambda: (
            verify_oracle_memory_observation_candidate_materialization_batch(
                replace(batch, qseries_execution_enabled=True)
            )
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-027 intake batch consumed")
    print("[PASS] Canonical OML-009 candidate contract consumed")
    print("[PASS] Certified observations materialized as candidates")
    print("[PASS] Observation payload lineage retained")
    print("[PASS] Evidence and parent lineage retained")
    print("[PASS] Source-certification lineage retained")
    print("[PASS] Duplicate candidate detected")
    print("[PASS] Downstream validation authorized read-only")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Materialization deterministic across replay")
    print("[PASS] Tampered materialization batches rejected")
    print(
        "[DONE] OML-028 CERTIFIED OBSERVATION "
        "CANDIDATE MATERIALIZATION PASS"
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
        CANDIDATE_MODULE,
        CANDIDATE_TEST,
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

    observation_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_intake_contract"
    )

    observation_expected = {
        "SCHEMA_VERSION": "OML-027",
        "ENGINE_ID": "OML-027",
        "POLICY_ID": (
            "oracle-memory.certified-observation-intake-contract.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-026",
        "UPSTREAM_ENGINE_ID": "OML-026",
    }

    for name, value in observation_expected.items():
        actual = getattr(observation_module, name, None)

        if actual != value:
            raise RuntimeError(
                f"Certified OML-027 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    candidate_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_canonical_record_candidate_contract"
    )

    required_candidate_symbols = (
        "OracleMemoryCanonicalRecordCandidate",
        "verify_oracle_memory_canonical_record_candidate",
    )

    missing = [
        name
        for name in required_candidate_symbols
        if not hasattr(candidate_module, name)
    ]

    if missing:
        raise RuntimeError(
            "Certified candidate contract missing symbols: "
            + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-028 FOR-SURE INSTALLER")
    print(" CERTIFIED OBSERVATION CANDIDATE MATERIALIZATION")
    print("=" * 48)
    print("[BOOT] Revision: REPOSITORY_ALIGNED_OBSERVATION_BRIDGE")

    try:
        validate_upstreams()
        print("[OK] Actual OML-027 imported and structurally verified")
        print("[OK] Actual canonical candidate contract verified")

        upstream_run = subprocess.run(
            [sys.executable, str(UPSTREAM_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream_run.returncode:
            raise RuntimeError(
                "OML-027 certification failed with exit code "
                f"{upstream_run.returncode}"
            )

        candidate_run = subprocess.run(
            [sys.executable, str(CANDIDATE_TEST)],
            cwd=ROOT,
            check=False,
        )

        if candidate_run.returncode:
            raise RuntimeError(
                "Canonical candidate certification failed with exit code "
                f"{candidate_run.returncode}"
            )

        upstream_before = UPSTREAM.read_bytes()
        upstream_test_before = UPSTREAM_TEST.read_bytes()
        candidate_before = CANDIDATE_MODULE.read_bytes()
        candidate_test_before = CANDIDATE_TEST.read_bytes()

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from ."
            "oracle_memory_certified_observation_candidate_materialization "
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
                "OML-028 test failed with exit code "
                f"{completed.returncode}"
            )

        if UPSTREAM.read_bytes() != upstream_before:
            raise RuntimeError("Certified OML-027 production changed")

        if UPSTREAM_TEST.read_bytes() != upstream_test_before:
            raise RuntimeError("Certified OML-027 standalone test changed")

        if CANDIDATE_MODULE.read_bytes() != candidate_before:
            raise RuntimeError("Certified candidate contract changed")

        if CANDIDATE_TEST.read_bytes() != candidate_test_before:
            raise RuntimeError("Certified candidate test changed")

        print("[PASS] Certified OML-027 production unchanged")
        print("[PASS] Certified OML-027 standalone test unchanged")
        print("[PASS] Canonical candidate production unchanged")
        print("[PASS] Canonical candidate standalone test unchanged")
        print("[PASS] OML-028 materialization installed")
        print("[PASS] OML-028 standalone deterministic test installed")
        print("[PASS] Observation-to-candidate bridge installed")
        print("[PASS] Evidence and source lineage preserved")
        print("[PASS] Duplicate materialization detection installed")
        print("[PASS] Downstream validation authorized read-only")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OML-028 CERTIFIED OBSERVATION "
            "CANDIDATE MATERIALIZATION INSTALLED"
        )
        return 0

    except (RuntimeError, SyntaxError, ImportError, KeyError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
