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
    / "oracle_memory_certified_observation_candidate_materialization.py"
)
UPSTREAM_TEST = (
    ROOT
    / "test_oml_028_oracle_memory_certified_observation_candidate_materialization.py"
)

VALIDATION_MODULE = (
    PACKAGE
    / "oracle_memory_candidate_validation_and_deduplication.py"
)
VALIDATION_TEST = (
    ROOT
    / "test_oml_017_oracle_memory_candidate_validation_and_deduplication.py"
)

PRODUCTION = (
    PACKAGE
    / "oracle_memory_certified_observation_candidate_validation_and_admission.py"
)
TEST = (
    ROOT
    / "test_oml_029_oracle_memory_certified_observation_candidate_validation_and_admission.py"
)
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    STATUS_DUPLICATE,
    STATUS_VALID,
    OracleMemoryCandidateValidationBatch,
    OracleMemoryCandidateValidationResult,
    verify_oracle_memory_candidate_validation_batch,
    verify_oracle_memory_candidate_validation_result,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_materialization import (
    MATERIALIZATION_STATUS_DUPLICATE,
    MATERIALIZATION_STATUS_READY,
    OracleMemoryObservationCandidateBinding,
    OracleMemoryObservationCandidateMaterializationBatch,
    verify_oracle_memory_observation_candidate_binding,
    verify_oracle_memory_observation_candidate_materialization_batch,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-029"
ENGINE_ID = "OML-029"
POLICY_ID = (
    "oracle-memory.certified-observation-candidate-validation-and-admission.v1"
)

UPSTREAM_SCHEMA_VERSION = "OML-028"
UPSTREAM_ENGINE_ID = "OML-028"

ADMISSION_STATUS_ADMITTED = "admitted"
ADMISSION_STATUS_REJECTED_DUPLICATE = "rejected_duplicate"

ALLOWED_ADMISSION_STATUSES = (
    ADMISSION_STATUS_ADMITTED,
    ADMISSION_STATUS_REJECTED_DUPLICATE,
)


class OracleMemoryObservationCandidateAdmissionInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryObservationCandidateAdmission:
    observation_hash: str
    candidate_hash: str
    validation_result_hash: str
    materialization_binding_hash: str
    admission_status: str
    duplicate_of_candidate_hash: str | None
    observation_lineage_verified: bool
    materialization_lineage_verified: bool
    validation_lineage_verified: bool
    evidence_lineage_verified: bool
    candidate_identity_verified: bool
    duplicate_policy_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    admission_hash: str


@dataclass(frozen=True)
class OracleMemoryObservationCandidateAdmissionBatch:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_batch_hash: str
    validation_batch_hash: str
    admissions: tuple[OracleMemoryObservationCandidateAdmission, ...]
    admission_count: int
    admitted_count: int
    rejected_duplicate_count: int
    canonical_order_verified: bool
    deterministic_admission_verified: bool
    materialization_lineage_verified: bool
    validation_lineage_verified: bool
    duplicate_policy_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    admission_ready: bool
    downstream_entity_resolution_authorized: bool
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

    raise OracleMemoryObservationCandidateAdmissionInvariantError(
        "unsupported OML-029 value type: "
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
    raise OracleMemoryObservationCandidateAdmissionInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-029 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryObservationCandidateAdmissionInvariantError(
            f"OML-029 invalid {label} hexadecimal value"
        ) from exc


def _build_admission(
    *,
    binding: OracleMemoryObservationCandidateBinding,
    validation_result: OracleMemoryCandidateValidationResult,
) -> OracleMemoryObservationCandidateAdmission:
    verify_oracle_memory_observation_candidate_binding(binding)
    verify_oracle_memory_candidate_validation_result(validation_result)

    if binding.candidate_hash != validation_result.candidate_hash:
        _reject("OML-029 candidate hash lineage mismatch")

    if binding.candidate_id != validation_result.candidate_id:
        _reject("OML-029 candidate id lineage mismatch")

    if binding.domain_id != validation_result.domain_id:
        _reject("OML-029 candidate domain lineage mismatch")

    duplicate = (
        binding.materialization_status == MATERIALIZATION_STATUS_DUPLICATE
        or validation_result.status == STATUS_DUPLICATE
    )

    if duplicate:
        admission_status = ADMISSION_STATUS_REJECTED_DUPLICATE
        duplicate_of = (
            validation_result.duplicate_of_candidate_hash
            or binding.duplicate_of_candidate_hash
        )
    else:
        admission_status = ADMISSION_STATUS_ADMITTED
        duplicate_of = None

    body = {
        "observation_hash": binding.observation_hash,
        "candidate_hash": binding.candidate_hash,
        "validation_result_hash": validation_result.result_hash,
        "materialization_binding_hash": binding.binding_hash,
        "admission_status": admission_status,
        "duplicate_of_candidate_hash": duplicate_of,
        "observation_lineage_verified": True,
        "materialization_lineage_verified": True,
        "validation_lineage_verified": True,
        "evidence_lineage_verified": (
            binding.evidence_lineage_verified
        ),
        "candidate_identity_verified": True,
        "duplicate_policy_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    admission = OracleMemoryObservationCandidateAdmission(
        **body,
        admission_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_candidate_admission(admission)
    return admission


def verify_oracle_memory_observation_candidate_admission(
    admission: OracleMemoryObservationCandidateAdmission,
) -> bool:
    body = asdict(admission)
    supplied = body.pop("admission_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-029 admission hash mismatch")

    for value, label in (
        (admission.observation_hash, "observation hash"),
        (admission.candidate_hash, "candidate hash"),
        (admission.validation_result_hash, "validation result hash"),
        (
            admission.materialization_binding_hash,
            "materialization binding hash",
        ),
        (admission.admission_hash, "admission hash"),
    ):
        _require_hash(value, label)

    if admission.admission_status not in ALLOWED_ADMISSION_STATUSES:
        _reject("OML-029 admission status invalid")

    if admission.admission_status == (
        ADMISSION_STATUS_REJECTED_DUPLICATE
    ):
        if admission.duplicate_of_candidate_hash is None:
            _reject("OML-029 duplicate admission lineage missing")
        _require_hash(
            admission.duplicate_of_candidate_hash,
            "duplicate candidate hash",
        )
    elif admission.duplicate_of_candidate_hash is not None:
        _reject("OML-029 unexpected duplicate lineage")

    required_true = (
        admission.observation_lineage_verified,
        admission.materialization_lineage_verified,
        admission.validation_lineage_verified,
        admission.evidence_lineage_verified,
        admission.candidate_identity_verified,
        admission.duplicate_policy_verified,
        admission.read_only,
    )

    if not all(required_true):
        _reject("OML-029 admission guarantee missing")

    forbidden = (
        admission.persistence_authorized,
        admission.learning_update_authorized,
        admission.runtime_activation_authorized,
        admission.publication_authorized,
        admission.action_authorization_enabled,
        admission.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-029 forbidden admission capability enabled")

    return True


def build_oracle_memory_observation_candidate_admission_batch(
    *,
    materialization_batch: (
        OracleMemoryObservationCandidateMaterializationBatch
    ),
    validation_batch: OracleMemoryCandidateValidationBatch,
) -> OracleMemoryObservationCandidateAdmissionBatch:
    verify_oracle_memory_observation_candidate_materialization_batch(
        materialization_batch
    )
    verify_oracle_memory_candidate_validation_batch(validation_batch)

    if materialization_batch.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-029 upstream schema mismatch")

    if materialization_batch.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-029 upstream engine mismatch")

    if not materialization_batch.materialization_ready:
        _reject("OML-029 materialization batch not ready")

    if not materialization_batch.downstream_validation_authorized:
        _reject("OML-029 downstream validation not authorized")

    if not materialization_batch.read_only:
        _reject("OML-029 materialization batch not read-only")

    if validation_batch.candidate_count != (
        materialization_batch.candidate_count
    ):
        _reject("OML-029 validation/materialization count mismatch")

    bindings_by_candidate_hash = {
        binding.candidate_hash: binding
        for binding in materialization_batch.bindings
    }

    results_by_candidate_hash: dict[
        str,
        list[OracleMemoryCandidateValidationResult],
    ] = {}

    for result in validation_batch.results:
        results_by_candidate_hash.setdefault(
            result.candidate_hash,
            [],
        ).append(result)

    admissions = []

    for binding in materialization_batch.bindings:
        candidates = results_by_candidate_hash.get(
            binding.candidate_hash,
            [],
        )

        if not candidates:
            _reject("OML-029 missing validation result")

        validation_result = candidates.pop(0)

        admissions.append(
            _build_admission(
                binding=binding,
                validation_result=validation_result,
            )
        )

    ordered = tuple(
        sorted(
            admissions,
            key=lambda item: (
                item.admission_status,
                item.observation_hash,
                item.candidate_hash,
                item.admission_hash,
            ),
        )
    )

    admitted_count = sum(
        item.admission_status == ADMISSION_STATUS_ADMITTED
        for item in ordered
    )
    rejected_count = sum(
        item.admission_status
        == ADMISSION_STATUS_REJECTED_DUPLICATE
        for item in ordered
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": materialization_batch.schema_version,
        "upstream_engine_id": materialization_batch.engine_id,
        "upstream_batch_hash": materialization_batch.batch_hash,
        "validation_batch_hash": validation_batch.batch_hash,
        "admissions": ordered,
        "admission_count": len(ordered),
        "admitted_count": admitted_count,
        "rejected_duplicate_count": rejected_count,
        "canonical_order_verified": True,
        "deterministic_admission_verified": True,
        "materialization_lineage_verified": True,
        "validation_lineage_verified": True,
        "duplicate_policy_verified": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "admission_ready": True,
        "downstream_entity_resolution_authorized": True,
        "read_only": True,
    }

    batch = OracleMemoryObservationCandidateAdmissionBatch(
        **body,
        batch_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_candidate_admission_batch(batch)
    return batch


def verify_oracle_memory_observation_candidate_admission_batch(
    batch: OracleMemoryObservationCandidateAdmissionBatch,
) -> bool:
    body = asdict(batch)
    supplied = body.pop("batch_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-029 batch hash mismatch")

    if batch.schema_version != SCHEMA_VERSION:
        _reject("OML-029 schema mismatch")

    if batch.engine_id != ENGINE_ID:
        _reject("OML-029 engine mismatch")

    if batch.policy_id != POLICY_ID:
        _reject("OML-029 policy mismatch")

    if batch.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-029 subsystem mismatch")

    if batch.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-029 upstream schema lineage mismatch")

    if batch.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-029 upstream engine lineage mismatch")

    if batch.admission_count != len(batch.admissions):
        _reject("OML-029 admission count mismatch")

    if (
        batch.admitted_count
        + batch.rejected_duplicate_count
        != batch.admission_count
    ):
        _reject("OML-029 admission reconciliation mismatch")

    for admission in batch.admissions:
        verify_oracle_memory_observation_candidate_admission(admission)

    required_true = (
        batch.canonical_order_verified,
        batch.deterministic_admission_verified,
        batch.materialization_lineage_verified,
        batch.validation_lineage_verified,
        batch.duplicate_policy_verified,
        batch.admission_ready,
        batch.downstream_entity_resolution_authorized,
        batch.read_only,
    )

    if not all(required_true):
        _reject("OML-029 batch guarantee missing")

    forbidden = (
        batch.persistence_enabled,
        batch.learning_updates_enabled,
        batch.runtime_activation_enabled,
        batch.publication_enabled,
        batch.action_authorization_enabled,
        batch.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-029 forbidden batch capability enabled")

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
    ADMISSION_STATUS_ADMITTED,
    ADMISSION_STATUS_REJECTED_DUPLICATE,
    OracleMemoryObservationCandidateAdmissionInvariantError,
    build_oracle_memory_observation_candidate_admission_batch,
    verify_oracle_memory_observation_candidate_admission_batch,
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
    except OracleMemoryObservationCandidateAdmissionInvariantError:
        return

    raise AssertionError(f"tampered OML-029 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-029 TEST")
    print(" CERTIFIED OBSERVATION CANDIDATE VALIDATION AND ADMISSION")
    print("=" * 48)

    root = Path(__file__).resolve().parent

    fixture_028 = load_module(
        root
        / "test_oml_028_oracle_memory_certified_observation_candidate_materialization.py",
        "oml_028_fixture_for_oml_029",
    )

    intake_batch = fixture_028.build_intake_batch(root)

    materialization_batch = (
        build_oracle_memory_observation_candidate_materialization_batch(
            intake_batch=intake_batch,
        )
    )

    fixture_016 = load_module(
        root
        / "test_oml_016_oracle_memory_ledger_integrity_and_replay_certification.py",
        "oml_016_fixture_for_oml_029",
    )

    ledger_contract = fixture_016.build_oml_015_contract(root)

    from qseries_v2.oracle_memory.oracle_memory_ledger_integrity_and_replay_certification import (
        build_oracle_memory_ledger_integrity_replay_certification,
    )

    ledger_certification = (
        build_oracle_memory_ledger_integrity_replay_certification(
            ledger_contract=ledger_contract,
        )
    )

    validation_batch = build_oracle_memory_candidate_validation_batch(
        ledger_certification=ledger_certification,
        candidates=materialization_batch.candidates,
    )

    batch = build_oracle_memory_observation_candidate_admission_batch(
        materialization_batch=materialization_batch,
        validation_batch=validation_batch,
    )

    assert batch.schema_version == "OML-029"
    assert batch.engine_id == "OML-029"
    assert batch.upstream_schema_version == "OML-028"
    assert batch.upstream_engine_id == "OML-028"
    assert batch.admission_count == 2
    assert batch.admitted_count == 1
    assert batch.rejected_duplicate_count == 1

    statuses = tuple(
        item.admission_status for item in batch.admissions
    )

    assert ADMISSION_STATUS_ADMITTED in statuses
    assert ADMISSION_STATUS_REJECTED_DUPLICATE in statuses
    assert batch.canonical_order_verified
    assert batch.deterministic_admission_verified
    assert batch.materialization_lineage_verified
    assert batch.validation_lineage_verified
    assert batch.duplicate_policy_verified
    assert not batch.persistence_enabled
    assert not batch.learning_updates_enabled
    assert not batch.runtime_activation_enabled
    assert not batch.publication_enabled
    assert not batch.action_authorization_enabled
    assert not batch.qseries_execution_enabled
    assert batch.admission_ready
    assert batch.downstream_entity_resolution_authorized
    assert batch.read_only

    replay = build_oracle_memory_observation_candidate_admission_batch(
        materialization_batch=materialization_batch,
        validation_batch=validation_batch,
    )

    assert replay == batch
    assert verify_oracle_memory_observation_candidate_admission_batch(
        batch
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_candidate_admission_batch(
            replace(batch, admitted_count=2)
        ),
        "admission count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_candidate_admission_batch(
            replace(batch, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_candidate_admission_batch(
            replace(
                batch,
                downstream_entity_resolution_authorized=False,
            )
        ),
        "entity-resolution authorization",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_candidate_admission_batch(
            replace(batch, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-028 materialization consumed")
    print("[PASS] Certified OML-017 validation engine consumed")
    print("[PASS] Observation-candidate lineage retained")
    print("[PASS] Validation-result lineage retained")
    print("[PASS] Unique candidate admitted")
    print("[PASS] Duplicate candidate rejected")
    print("[PASS] Evidence lineage retained")
    print("[PASS] Downstream entity resolution authorized read-only")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Admission deterministic across replay")
    print("[PASS] Tampered admission batches rejected")
    print(
        "[DONE] OML-029 CERTIFIED OBSERVATION "
        "CANDIDATE VALIDATION AND ADMISSION PASS"
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
        VALIDATION_MODULE,
        VALIDATION_TEST,
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

    materialization_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_candidate_materialization"
    )

    expected = {
        "SCHEMA_VERSION": "OML-028",
        "ENGINE_ID": "OML-028",
        "POLICY_ID": (
            "oracle-memory.certified-observation-candidate-materialization.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-027",
        "UPSTREAM_ENGINE_ID": "OML-027",
    }

    for name, value in expected.items():
        actual = getattr(materialization_module, name, None)

        if actual != value:
            raise RuntimeError(
                f"Certified OML-028 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    validation_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_candidate_validation_and_deduplication"
    )

    required_validation_symbols = (
        "OracleMemoryCandidateValidationBatch",
        "OracleMemoryCandidateValidationResult",
        "build_oracle_memory_candidate_validation_batch",
        "verify_oracle_memory_candidate_validation_batch",
    )

    missing = [
        name
        for name in required_validation_symbols
        if not hasattr(validation_module, name)
    ]

    if missing:
        raise RuntimeError(
            "Certified validation engine missing symbols: "
            + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-029 FOR-SURE INSTALLER")
    print(" CERTIFIED OBSERVATION CANDIDATE VALIDATION AND ADMISSION")
    print("=" * 48)
    print("[BOOT] Revision: REPOSITORY_ALIGNED_OBSERVATION_BRIDGE")

    try:
        validate_upstreams()
        print("[OK] Actual OML-028 imported and structurally verified")
        print("[OK] Actual OML-017 validation engine verified")

        upstream_run = subprocess.run(
            [sys.executable, str(UPSTREAM_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream_run.returncode:
            raise RuntimeError(
                "OML-028 certification failed with exit code "
                f"{upstream_run.returncode}"
            )

        validation_run = subprocess.run(
            [sys.executable, str(VALIDATION_TEST)],
            cwd=ROOT,
            check=False,
        )

        if validation_run.returncode:
            raise RuntimeError(
                "OML-017 validation certification failed with exit code "
                f"{validation_run.returncode}"
            )

        upstream_before = UPSTREAM.read_bytes()
        upstream_test_before = UPSTREAM_TEST.read_bytes()
        validation_before = VALIDATION_MODULE.read_bytes()
        validation_test_before = VALIDATION_TEST.read_bytes()

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from ."
            "oracle_memory_certified_observation_candidate_validation_and_admission "
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
                "OML-029 test failed with exit code "
                f"{completed.returncode}"
            )

        if UPSTREAM.read_bytes() != upstream_before:
            raise RuntimeError("Certified OML-028 production changed")

        if UPSTREAM_TEST.read_bytes() != upstream_test_before:
            raise RuntimeError("Certified OML-028 standalone test changed")

        if VALIDATION_MODULE.read_bytes() != validation_before:
            raise RuntimeError("Certified OML-017 production changed")

        if VALIDATION_TEST.read_bytes() != validation_test_before:
            raise RuntimeError("Certified OML-017 standalone test changed")

        print("[PASS] Certified OML-028 production unchanged")
        print("[PASS] Certified OML-028 standalone test unchanged")
        print("[PASS] Certified OML-017 production unchanged")
        print("[PASS] Certified OML-017 standalone test unchanged")
        print("[PASS] OML-029 admission layer installed")
        print("[PASS] OML-029 standalone deterministic test installed")
        print("[PASS] Observation-candidate validation bridge installed")
        print("[PASS] Duplicate admission rejection installed")
        print("[PASS] Entity-resolution continuation authorized")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OML-029 CERTIFIED OBSERVATION "
            "CANDIDATE VALIDATION AND ADMISSION INSTALLED"
        )
        return 0

    except (RuntimeError, SyntaxError, ImportError, KeyError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
