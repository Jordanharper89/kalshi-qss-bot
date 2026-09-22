from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def locate_repository() -> Path:
    candidates: list[Path] = []

    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.extend((base, base / "kalshi-qss-bot"))
        for parent in base.parents:
            candidates.extend((parent, parent / "kalshi-qss-bot"))

    seen: set[Path] = set()

    for candidate in candidates:
        candidate = candidate.resolve()

        if candidate in seen:
            continue

        seen.add(candidate)

        upstream = (
            candidate
            / "qseries_v2"
            / "oracle_memory"
            / "oracle_memory_canonical_record_candidate_admission_registry_gate.py"
        )
        upstream_test = (
            candidate
            / "test_oml_012_oracle_memory_canonical_record_candidate_admission_registry_gate.py"
        )

        if upstream.is_file() and upstream_test.is_file():
            return candidate

    raise RuntimeError(
        "Could not locate repository containing certified OML-012."
    )


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

OML_012 = (
    PACKAGE
    / "oracle_memory_canonical_record_candidate_admission_registry_gate.py"
)
OML_012_TEST = (
    ROOT
    / "test_oml_012_oracle_memory_canonical_record_candidate_admission_registry_gate.py"
)

PRODUCTION = PACKAGE / "oracle_memory_store_contract.py"
TEST = ROOT / "test_oml_013_oracle_memory_store_contract.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_admission_registry_gate import (
    OracleMemoryCanonicalRecordCandidateAdmissionRegistryGateDecision,
    verify_oracle_memory_canonical_record_candidate_admission_registry_gate_decision,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-013"
ENGINE_ID = "OML-013"
POLICY_ID = "oracle-memory.store-contract.v1"

UPSTREAM_SCHEMA_VERSION = "OML-012"
UPSTREAM_ENGINE_ID = "OML-012"

STORE_MODE_APPEND_ONLY = "append_only"
STORE_STATE_CONTRACT_ONLY = "contract_only"
ATOMICITY_MODEL_SINGLE_COMMIT = "single_commit"
REPLAY_MODEL_FULL_LEDGER_REPLAY = "full_ledger_replay"


class OracleMemoryStoreContractInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryStorePartitionContract:
    domain_id: str
    ordinal: int
    partition_key: str
    append_only_required: bool
    deterministic_order_required: bool
    immutable_record_hash_required: bool
    parent_lineage_required: bool
    evidence_lineage_required: bool
    duplicate_record_hashes_forbidden: bool
    destructive_update_allowed: bool
    delete_allowed: bool
    persistence_enabled: bool
    learning_update_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    read_only: bool
    partition_hash: str


@dataclass(frozen=True)
class OracleMemoryStoreContractCertification:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_gate_decision_hash: str
    upstream_registry_hash: str
    certified_domain_ids: tuple[str, ...]
    store_mode: str
    store_state: str
    atomicity_model: str
    replay_model: str
    partitions: tuple[OracleMemoryStorePartitionContract, ...]
    partition_count: int
    canonical_serialization_required: bool
    deterministic_commit_hashing_required: bool
    append_only_required: bool
    immutable_ledger_required: bool
    atomic_commit_required: bool
    replay_verification_required: bool
    lineage_preservation_required: bool
    duplicate_record_hashes_forbidden: bool
    destructive_updates_forbidden: bool
    deletes_forbidden: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    database_access_enabled: bool
    networking_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    contract_ready: bool
    next_certification_authorized: bool
    read_only: bool
    certification_hash: str


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

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    raise OracleMemoryStoreContractInvariantError(
        "unsupported OML-013 value type: "
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
    raise OracleMemoryStoreContractInvariantError(reason)


def _build_partition(
    *,
    domain_id: str,
    ordinal: int,
) -> OracleMemoryStorePartitionContract:
    body = {
        "domain_id": domain_id,
        "ordinal": ordinal,
        "partition_key": f"oracle-memory:{domain_id}",
        "append_only_required": True,
        "deterministic_order_required": True,
        "immutable_record_hash_required": True,
        "parent_lineage_required": True,
        "evidence_lineage_required": True,
        "duplicate_record_hashes_forbidden": True,
        "destructive_update_allowed": False,
        "delete_allowed": False,
        "persistence_enabled": False,
        "learning_update_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "read_only": True,
    }

    return OracleMemoryStorePartitionContract(
        **body,
        partition_hash=_stable_hash(body),
    )


def verify_oracle_memory_store_partition_contract(
    partition: OracleMemoryStorePartitionContract,
) -> bool:
    body = asdict(partition)
    supplied = body.pop("partition_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-013 partition hash mismatch")

    if partition.domain_id not in MEMORY_DOMAINS:
        _reject("OML-013 unknown memory domain")

    if partition.ordinal != MEMORY_DOMAINS.index(partition.domain_id) + 1:
        _reject("OML-013 partition ordinal mismatch")

    if partition.partition_key != f"oracle-memory:{partition.domain_id}":
        _reject("OML-013 partition key mismatch")

    required_true = (
        partition.append_only_required,
        partition.deterministic_order_required,
        partition.immutable_record_hash_required,
        partition.parent_lineage_required,
        partition.evidence_lineage_required,
        partition.duplicate_record_hashes_forbidden,
        partition.read_only,
    )

    if not all(required_true):
        _reject("OML-013 partition guarantee missing")

    forbidden = (
        partition.destructive_update_allowed,
        partition.delete_allowed,
        partition.persistence_enabled,
        partition.learning_update_enabled,
        partition.runtime_activation_enabled,
        partition.publication_enabled,
        partition.action_authorization_enabled,
        partition.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-013 forbidden partition capability enabled")

    return True


def build_oracle_memory_store_contract_certification(
    *,
    gate_decision: OracleMemoryCanonicalRecordCandidateAdmissionRegistryGateDecision,
) -> OracleMemoryStoreContractCertification:
    verify_oracle_memory_canonical_record_candidate_admission_registry_gate_decision(
        gate_decision
    )

    if gate_decision.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-013 upstream schema mismatch")

    if gate_decision.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-013 upstream engine mismatch")

    if not gate_decision.admitted:
        _reject("OML-013 upstream gate not admitted")

    if not gate_decision.next_certification_authorized:
        _reject("OML-013 upstream continuation not authorized")

    if not gate_decision.read_only:
        _reject("OML-013 upstream read-only guarantee missing")

    if gate_decision.admitted_domain_ids != MEMORY_DOMAINS:
        _reject("OML-013 upstream domain identity mismatch")

    partitions = tuple(
        _build_partition(
            domain_id=domain_id,
            ordinal=index,
        )
        for index, domain_id in enumerate(MEMORY_DOMAINS, start=1)
    )

    for partition in partitions:
        verify_oracle_memory_store_partition_contract(partition)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": gate_decision.schema_version,
        "upstream_engine_id": gate_decision.engine_id,
        "upstream_gate_decision_hash": gate_decision.decision_hash,
        "upstream_registry_hash": gate_decision.upstream_registry_hash,
        "certified_domain_ids": gate_decision.admitted_domain_ids,
        "store_mode": STORE_MODE_APPEND_ONLY,
        "store_state": STORE_STATE_CONTRACT_ONLY,
        "atomicity_model": ATOMICITY_MODEL_SINGLE_COMMIT,
        "replay_model": REPLAY_MODEL_FULL_LEDGER_REPLAY,
        "partitions": partitions,
        "partition_count": len(partitions),
        "canonical_serialization_required": True,
        "deterministic_commit_hashing_required": True,
        "append_only_required": True,
        "immutable_ledger_required": True,
        "atomic_commit_required": True,
        "replay_verification_required": True,
        "lineage_preservation_required": True,
        "duplicate_record_hashes_forbidden": True,
        "destructive_updates_forbidden": True,
        "deletes_forbidden": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "database_access_enabled": False,
        "networking_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "contract_ready": True,
        "next_certification_authorized": True,
        "read_only": True,
    }

    certification = OracleMemoryStoreContractCertification(
        **body,
        certification_hash=_stable_hash(body),
    )

    verify_oracle_memory_store_contract_certification(certification)
    return certification


def verify_oracle_memory_store_contract_certification(
    certification: OracleMemoryStoreContractCertification,
) -> bool:
    body = asdict(certification)
    supplied = body.pop("certification_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-013 certification hash mismatch")

    if certification.schema_version != SCHEMA_VERSION:
        _reject("OML-013 certification schema mismatch")

    if certification.engine_id != ENGINE_ID:
        _reject("OML-013 certification engine mismatch")

    if certification.policy_id != POLICY_ID:
        _reject("OML-013 certification policy mismatch")

    if certification.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-013 certification subsystem mismatch")

    if certification.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-013 certification upstream schema mismatch")

    if certification.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-013 certification upstream engine mismatch")

    if certification.certified_domain_ids != MEMORY_DOMAINS:
        _reject("OML-013 certification domain mismatch")

    if certification.partition_count != len(MEMORY_DOMAINS):
        _reject("OML-013 partition count mismatch")

    if tuple(item.domain_id for item in certification.partitions) != MEMORY_DOMAINS:
        _reject("OML-013 partition order mismatch")

    for partition in certification.partitions:
        verify_oracle_memory_store_partition_contract(partition)

    if certification.store_mode != STORE_MODE_APPEND_ONLY:
        _reject("OML-013 store mode mismatch")

    if certification.store_state != STORE_STATE_CONTRACT_ONLY:
        _reject("OML-013 store state mismatch")

    if certification.atomicity_model != ATOMICITY_MODEL_SINGLE_COMMIT:
        _reject("OML-013 atomicity model mismatch")

    if certification.replay_model != REPLAY_MODEL_FULL_LEDGER_REPLAY:
        _reject("OML-013 replay model mismatch")

    required_true = (
        certification.canonical_serialization_required,
        certification.deterministic_commit_hashing_required,
        certification.append_only_required,
        certification.immutable_ledger_required,
        certification.atomic_commit_required,
        certification.replay_verification_required,
        certification.lineage_preservation_required,
        certification.duplicate_record_hashes_forbidden,
        certification.destructive_updates_forbidden,
        certification.deletes_forbidden,
        certification.contract_ready,
        certification.next_certification_authorized,
        certification.read_only,
    )

    if not all(required_true):
        _reject("OML-013 certification guarantee missing")

    forbidden = (
        certification.persistence_enabled,
        certification.learning_updates_enabled,
        certification.runtime_activation_enabled,
        certification.database_access_enabled,
        certification.networking_enabled,
        certification.publication_enabled,
        certification.action_authorization_enabled,
        certification.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-013 forbidden store capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_canonical_record_admission_registry import (
    build_oracle_memory_canonical_record_admission_registry,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_admission_registry_gate import (
    build_oracle_memory_canonical_record_admission_registry_gate_decision,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_admission_registry import (
    build_oracle_memory_canonical_record_candidate_admission_registry,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_admission_registry_gate import (
    build_oracle_memory_canonical_record_candidate_admission_registry_gate_decision,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract import (
    build_oracle_memory_canonical_record_candidate_contract_certification,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract_admission_gate import (
    build_oracle_memory_canonical_record_candidate_contract_admission_decision,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_contract import (
    build_oracle_memory_canonical_record_contract_certification,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_contract_admission_gate import (
    build_oracle_memory_canonical_record_contract_admission_decision,
)
from qseries_v2.oracle_memory.oracle_memory_certified_domain_registry import (
    build_oracle_memory_certified_domain_registry,
)
from qseries_v2.oracle_memory.oracle_memory_certified_domain_registry_admission_gate import (
    build_oracle_memory_domain_registry_admission_decision,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    build_oracle_memory_learner_foundation_report,
)
from qseries_v2.oracle_memory.oracle_memory_learner_foundation_admission_gate import (
    build_oracle_memory_learner_foundation_admission_decision,
)
from qseries_v2.oracle_memory.oracle_memory_store_contract import (
    OracleMemoryStoreContractInvariantError,
    build_oracle_memory_store_contract_certification,
    verify_oracle_memory_store_contract_certification,
)


def load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)

    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")

    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def build_oml_012_decision(root: Path):
    fixture = load_module(
        root
        / "test_oit_050_oracle_terminal_final_freeze_and_completion.py",
        "oit_050_fixture_for_oml_013",
    )

    from qseries_v2.oracle_terminal.oracle_terminal_final_freeze_and_completion import (
        build_oracle_terminal_final_freeze_completion_report,
    )

    oit_049 = fixture.build_oit_049_report(root)
    oit_050 = build_oracle_terminal_final_freeze_completion_report(
        root,
        production_certification_report=oit_049,
    )
    oml_001 = build_oracle_memory_learner_foundation_report(
        root,
        oit_final_freeze_report=oit_050,
    )
    oml_002 = build_oracle_memory_learner_foundation_admission_decision(
        root,
        foundation_report=oml_001,
    )
    oml_003 = build_oracle_memory_certified_domain_registry(
        admission_decision=oml_002,
    )
    oml_004 = build_oracle_memory_domain_registry_admission_decision(
        registry=oml_003,
    )
    oml_005 = build_oracle_memory_canonical_record_contract_certification(
        admission_decision=oml_004,
    )
    oml_006 = build_oracle_memory_canonical_record_contract_admission_decision(
        certification=oml_005,
    )
    oml_007 = build_oracle_memory_canonical_record_admission_registry(
        admission_decision=oml_006,
    )
    oml_008 = build_oracle_memory_canonical_record_admission_registry_gate_decision(
        registry=oml_007,
    )
    oml_009 = build_oracle_memory_canonical_record_candidate_contract_certification(
        gate_decision=oml_008,
    )
    oml_010 = build_oracle_memory_canonical_record_candidate_contract_admission_decision(
        certification=oml_009,
    )
    oml_011 = build_oracle_memory_canonical_record_candidate_admission_registry(
        admission_decision=oml_010,
    )

    return build_oracle_memory_canonical_record_candidate_admission_registry_gate_decision(
        registry=oml_011,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryStoreContractInvariantError:
        return

    raise AssertionError(f"tampered OML-013 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-013 TEST")
    print(" MEMORY STORE CONTRACT")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    gate = build_oml_012_decision(root)

    certification = build_oracle_memory_store_contract_certification(
        gate_decision=gate,
    )

    assert certification.schema_version == "OML-013"
    assert certification.engine_id == "OML-013"
    assert certification.upstream_schema_version == "OML-012"
    assert certification.upstream_engine_id == "OML-012"
    assert certification.upstream_gate_decision_hash == gate.decision_hash
    assert certification.certified_domain_ids == MEMORY_DOMAINS
    assert certification.partition_count == 8
    assert certification.store_mode == "append_only"
    assert certification.store_state == "contract_only"
    assert certification.atomicity_model == "single_commit"
    assert certification.replay_model == "full_ledger_replay"
    assert certification.append_only_required
    assert certification.immutable_ledger_required
    assert certification.atomic_commit_required
    assert certification.replay_verification_required
    assert certification.lineage_preservation_required
    assert certification.destructive_updates_forbidden
    assert certification.deletes_forbidden
    assert not certification.persistence_enabled
    assert not certification.learning_updates_enabled
    assert not certification.runtime_activation_enabled
    assert not certification.database_access_enabled
    assert not certification.networking_enabled
    assert not certification.publication_enabled
    assert not certification.action_authorization_enabled
    assert not certification.qseries_execution_enabled
    assert certification.contract_ready
    assert certification.next_certification_authorized
    assert certification.read_only

    replay = build_oracle_memory_store_contract_certification(
        gate_decision=gate,
    )

    assert replay == certification
    assert verify_oracle_memory_store_contract_certification(
        certification
    )

    expect_rejection(
        lambda: verify_oracle_memory_store_contract_certification(
            replace(certification, append_only_required=False)
        ),
        "append-only guarantee",
    )

    expect_rejection(
        lambda: verify_oracle_memory_store_contract_certification(
            replace(certification, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_store_contract_certification(
            replace(certification, destructive_updates_forbidden=False)
        ),
        "destructive update boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_store_contract_certification(
            replace(certification, qseries_execution_enabled=True)
        ),
        "Q Series execution boundary",
    )

    print("[PASS] Certified OML-012 gate consumed")
    print("[PASS] OML-012 through OIT-050 lineage retained")
    print("[PASS] Append-only memory store contract created")
    print("[PASS] Eight canonical store partitions defined")
    print("[PASS] Deterministic commit hashing required")
    print("[PASS] Atomic single-commit model required")
    print("[PASS] Full-ledger replay verification required")
    print("[PASS] Immutable ledger and lineage required")
    print("[PASS] Destructive updates and deletes forbidden")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Database and networking remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Contract deterministic across replay")
    print("[PASS] Tampered store certifications rejected")
    print("[DONE] OML-013 MEMORY STORE CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_actual_oml_012() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_canonical_record_candidate_admission_registry_gate"
    )

    expected = {
        "SCHEMA_VERSION": "OML-012",
        "ENGINE_ID": "OML-012",
        "POLICY_ID": (
            "oracle-memory.canonical-record-candidate-admission-registry-gate.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-011",
        "UPSTREAM_ENGINE_ID": "OML-011",
        "GATE_STATUS_ADMITTED": "admitted",
    }

    for name, value in expected.items():
        actual = getattr(module, name, None)

        if actual != value:
            raise RuntimeError(
                f"Certified OML-012 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    required = (
        "OracleMemoryCanonicalRecordCandidateAdmissionRegistryGateDecision",
        "build_oracle_memory_canonical_record_candidate_admission_registry_gate_decision",
        "verify_oracle_memory_canonical_record_candidate_admission_registry_gate_decision",
    )

    missing = [name for name in required if not hasattr(module, name)]

    if missing:
        raise RuntimeError(
            "Certified OML-012 missing required symbols: "
            + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-013 FOR-SURE INSTALLER")
    print(" MEMORY STORE CONTRACT")
    print("=" * 48)
    print("[BOOT] Revision: CAPABILITY_MILESTONE_FULL_REPLACEMENT")

    try:
        validate_actual_oml_012()
        print("[OK] Actual OML-012 imported and structurally verified")

        upstream = subprocess.run(
            [sys.executable, str(OML_012_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream.returncode:
            raise RuntimeError(
                "OML-012 certification failed with exit code "
                f"{upstream.returncode}"
            )

        production_before = OML_012.read_bytes()
        test_before = OML_012_TEST.read_bytes()

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = "from .oracle_memory_store_contract import *"
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
                "OML-013 test failed with exit code "
                f"{completed.returncode}"
            )

        if OML_012.read_bytes() != production_before:
            raise RuntimeError("Certified OML-012 production changed")

        if OML_012_TEST.read_bytes() != test_before:
            raise RuntimeError("Certified OML-012 standalone test changed")

        print("[PASS] Certified OML-012 production unchanged")
        print("[PASS] Certified OML-012 standalone test unchanged")
        print("[PASS] OML-013 memory store contract installed")
        print("[PASS] OML-013 standalone deterministic test installed")
        print("[PASS] Append-only store architecture defined")
        print("[PASS] Eight store partitions defined")
        print("[PASS] Atomicity and replay guarantees defined")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Database and networking remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OML-013 MEMORY STORE CONTRACT INSTALLED")
        return 0

    except (RuntimeError, SyntaxError, ImportError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
