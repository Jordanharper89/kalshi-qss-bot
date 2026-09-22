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
            / "oracle_memory_store_contract.py"
        )
        upstream_test = (
            candidate
            / "test_oml_013_oracle_memory_store_contract.py"
        )

        if upstream.is_file() and upstream_test.is_file():
            return candidate

    raise RuntimeError(
        "Could not locate repository containing certified OML-013."
    )


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

OML_013 = PACKAGE / "oracle_memory_store_contract.py"
OML_013_TEST = ROOT / "test_oml_013_oracle_memory_store_contract.py"

PRODUCTION = (
    PACKAGE
    / "oracle_memory_store_admission_and_atomicity_certification.py"
)
TEST = (
    ROOT
    / "test_oml_014_oracle_memory_store_admission_and_atomicity_certification.py"
)
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_store_contract import (
    ATOMICITY_MODEL_SINGLE_COMMIT,
    REPLAY_MODEL_FULL_LEDGER_REPLAY,
    STORE_MODE_APPEND_ONLY,
    STORE_STATE_CONTRACT_ONLY,
    OracleMemoryStoreContractCertification,
    verify_oracle_memory_store_contract_certification,
)

SCHEMA_VERSION = "OML-014"
ENGINE_ID = "OML-014"
POLICY_ID = "oracle-memory.store-admission-and-atomicity-certification.v1"

UPSTREAM_SCHEMA_VERSION = "OML-013"
UPSTREAM_ENGINE_ID = "OML-013"

ADMISSION_STATUS_CERTIFIED = "certified"
ATOMICITY_STATUS_CERTIFIED = "single_commit_atomicity_certified"


class OracleMemoryStoreAdmissionAtomicityInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryStorePartitionAdmission:
    domain_id: str
    ordinal: int
    upstream_partition_hash: str
    partition_key: str
    append_only_admitted: bool
    deterministic_order_admitted: bool
    immutable_record_hash_admitted: bool
    parent_lineage_admitted: bool
    evidence_lineage_admitted: bool
    duplicate_record_rejection_admitted: bool
    destructive_update_rejected: bool
    delete_rejected: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    admission_hash: str


@dataclass(frozen=True)
class OracleMemoryStoreAdmissionAtomicityCertification:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_gate_decision_hash: str
    upstream_registry_hash: str
    certified_domain_ids: tuple[str, ...]
    admission_status: str
    atomicity_status: str
    store_mode: str
    atomicity_model: str
    replay_model: str
    partition_admissions: tuple[OracleMemoryStorePartitionAdmission, ...]
    partition_count: int
    append_only_admitted: bool
    deterministic_commit_hashing_admitted: bool
    immutable_ledger_admitted: bool
    atomic_single_commit_admitted: bool
    full_replay_admitted: bool
    lineage_preservation_admitted: bool
    duplicate_record_rejection_admitted: bool
    destructive_updates_rejected: bool
    deletes_rejected: bool
    rollback_on_failure_required: bool
    partial_commit_forbidden: bool
    commit_order_canonical: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    database_access_enabled: bool
    networking_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    certification_ready: bool
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

    raise OracleMemoryStoreAdmissionAtomicityInvariantError(
        "unsupported OML-014 value type: "
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
    raise OracleMemoryStoreAdmissionAtomicityInvariantError(reason)


def _build_partition_admission(
    *,
    domain_id: str,
    ordinal: int,
    upstream_partition_hash: str,
    partition_key: str,
) -> OracleMemoryStorePartitionAdmission:
    body = {
        "domain_id": domain_id,
        "ordinal": ordinal,
        "upstream_partition_hash": upstream_partition_hash,
        "partition_key": partition_key,
        "append_only_admitted": True,
        "deterministic_order_admitted": True,
        "immutable_record_hash_admitted": True,
        "parent_lineage_admitted": True,
        "evidence_lineage_admitted": True,
        "duplicate_record_rejection_admitted": True,
        "destructive_update_rejected": True,
        "delete_rejected": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    return OracleMemoryStorePartitionAdmission(
        **body,
        admission_hash=_stable_hash(body),
    )


def verify_oracle_memory_store_partition_admission(
    admission: OracleMemoryStorePartitionAdmission,
) -> bool:
    body = asdict(admission)
    supplied = body.pop("admission_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-014 partition admission hash mismatch")

    if admission.domain_id not in MEMORY_DOMAINS:
        _reject("OML-014 unknown memory domain")

    if admission.ordinal != MEMORY_DOMAINS.index(admission.domain_id) + 1:
        _reject("OML-014 partition ordinal mismatch")

    if len(admission.upstream_partition_hash) != 64:
        _reject("OML-014 upstream partition hash invalid")

    if admission.partition_key != f"oracle-memory:{admission.domain_id}":
        _reject("OML-014 partition key mismatch")

    required_true = (
        admission.append_only_admitted,
        admission.deterministic_order_admitted,
        admission.immutable_record_hash_admitted,
        admission.parent_lineage_admitted,
        admission.evidence_lineage_admitted,
        admission.duplicate_record_rejection_admitted,
        admission.destructive_update_rejected,
        admission.delete_rejected,
        admission.read_only,
    )

    if not all(required_true):
        _reject("OML-014 partition admission guarantee missing")

    forbidden = (
        admission.persistence_authorized,
        admission.learning_update_authorized,
        admission.runtime_activation_authorized,
        admission.publication_authorized,
        admission.action_authorization_enabled,
        admission.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-014 forbidden partition capability enabled")

    return True


def build_oracle_memory_store_admission_atomicity_certification(
    *,
    store_contract: OracleMemoryStoreContractCertification,
) -> OracleMemoryStoreAdmissionAtomicityCertification:
    verify_oracle_memory_store_contract_certification(store_contract)

    if store_contract.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-014 upstream schema mismatch")

    if store_contract.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-014 upstream engine mismatch")

    if not store_contract.contract_ready:
        _reject("OML-014 upstream store contract not ready")

    if not store_contract.next_certification_authorized:
        _reject("OML-014 upstream continuation not authorized")

    if not store_contract.read_only:
        _reject("OML-014 upstream read-only guarantee missing")

    if store_contract.certified_domain_ids != MEMORY_DOMAINS:
        _reject("OML-014 upstream domain identity mismatch")

    admissions = tuple(
        _build_partition_admission(
            domain_id=partition.domain_id,
            ordinal=partition.ordinal,
            upstream_partition_hash=partition.partition_hash,
            partition_key=partition.partition_key,
        )
        for partition in store_contract.partitions
    )

    for admission in admissions:
        verify_oracle_memory_store_partition_admission(admission)

    domain_ids = tuple(item.domain_id for item in admissions)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": store_contract.schema_version,
        "upstream_engine_id": store_contract.engine_id,
        "upstream_certification_hash": store_contract.certification_hash,
        "upstream_gate_decision_hash": (
            store_contract.upstream_gate_decision_hash
        ),
        "upstream_registry_hash": store_contract.upstream_registry_hash,
        "certified_domain_ids": store_contract.certified_domain_ids,
        "admission_status": ADMISSION_STATUS_CERTIFIED,
        "atomicity_status": ATOMICITY_STATUS_CERTIFIED,
        "store_mode": store_contract.store_mode,
        "atomicity_model": store_contract.atomicity_model,
        "replay_model": store_contract.replay_model,
        "partition_admissions": admissions,
        "partition_count": len(admissions),
        "append_only_admitted": store_contract.append_only_required,
        "deterministic_commit_hashing_admitted": (
            store_contract.deterministic_commit_hashing_required
        ),
        "immutable_ledger_admitted": (
            store_contract.immutable_ledger_required
        ),
        "atomic_single_commit_admitted": (
            store_contract.atomic_commit_required
        ),
        "full_replay_admitted": (
            store_contract.replay_verification_required
        ),
        "lineage_preservation_admitted": (
            store_contract.lineage_preservation_required
        ),
        "duplicate_record_rejection_admitted": (
            store_contract.duplicate_record_hashes_forbidden
        ),
        "destructive_updates_rejected": (
            store_contract.destructive_updates_forbidden
        ),
        "deletes_rejected": store_contract.deletes_forbidden,
        "rollback_on_failure_required": True,
        "partial_commit_forbidden": True,
        "commit_order_canonical": domain_ids == MEMORY_DOMAINS,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "database_access_enabled": False,
        "networking_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "certification_ready": True,
        "next_certification_authorized": True,
        "read_only": True,
    }

    certification = OracleMemoryStoreAdmissionAtomicityCertification(
        **body,
        certification_hash=_stable_hash(body),
    )

    verify_oracle_memory_store_admission_atomicity_certification(
        certification
    )
    return certification


def verify_oracle_memory_store_admission_atomicity_certification(
    certification: OracleMemoryStoreAdmissionAtomicityCertification,
) -> bool:
    body = asdict(certification)
    supplied = body.pop("certification_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-014 certification hash mismatch")

    if certification.schema_version != SCHEMA_VERSION:
        _reject("OML-014 certification schema mismatch")

    if certification.engine_id != ENGINE_ID:
        _reject("OML-014 certification engine mismatch")

    if certification.policy_id != POLICY_ID:
        _reject("OML-014 certification policy mismatch")

    if certification.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-014 certification subsystem mismatch")

    if certification.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-014 certification upstream schema mismatch")

    if certification.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-014 certification upstream engine mismatch")

    if certification.certified_domain_ids != MEMORY_DOMAINS:
        _reject("OML-014 certification domain mismatch")

    if certification.partition_count != len(MEMORY_DOMAINS):
        _reject("OML-014 partition count mismatch")

    if tuple(
        item.domain_id
        for item in certification.partition_admissions
    ) != MEMORY_DOMAINS:
        _reject("OML-014 partition admission order mismatch")

    for admission in certification.partition_admissions:
        verify_oracle_memory_store_partition_admission(admission)

    if certification.admission_status != ADMISSION_STATUS_CERTIFIED:
        _reject("OML-014 admission status mismatch")

    if certification.atomicity_status != ATOMICITY_STATUS_CERTIFIED:
        _reject("OML-014 atomicity status mismatch")

    if certification.store_mode != STORE_MODE_APPEND_ONLY:
        _reject("OML-014 store mode mismatch")

    if certification.atomicity_model != ATOMICITY_MODEL_SINGLE_COMMIT:
        _reject("OML-014 atomicity model mismatch")

    if certification.replay_model != REPLAY_MODEL_FULL_LEDGER_REPLAY:
        _reject("OML-014 replay model mismatch")

    required_true = (
        certification.append_only_admitted,
        certification.deterministic_commit_hashing_admitted,
        certification.immutable_ledger_admitted,
        certification.atomic_single_commit_admitted,
        certification.full_replay_admitted,
        certification.lineage_preservation_admitted,
        certification.duplicate_record_rejection_admitted,
        certification.destructive_updates_rejected,
        certification.deletes_rejected,
        certification.rollback_on_failure_required,
        certification.partial_commit_forbidden,
        certification.commit_order_canonical,
        certification.certification_ready,
        certification.next_certification_authorized,
        certification.read_only,
    )

    if not all(required_true):
        _reject("OML-014 certification guarantee missing")

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
        _reject("OML-014 forbidden store capability enabled")

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
from qseries_v2.oracle_memory.oracle_memory_store_admission_and_atomicity_certification import (
    OracleMemoryStoreAdmissionAtomicityInvariantError,
    build_oracle_memory_store_admission_atomicity_certification,
    verify_oracle_memory_store_admission_atomicity_certification,
)
from qseries_v2.oracle_memory.oracle_memory_store_contract import (
    build_oracle_memory_store_contract_certification,
)


def load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)

    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")

    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def build_oml_013_contract(root: Path):
    fixture = load_module(
        root
        / "test_oit_050_oracle_terminal_final_freeze_and_completion.py",
        "oit_050_fixture_for_oml_014",
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
    oml_012 = build_oracle_memory_canonical_record_candidate_admission_registry_gate_decision(
        registry=oml_011,
    )

    return build_oracle_memory_store_contract_certification(
        gate_decision=oml_012,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryStoreAdmissionAtomicityInvariantError:
        return

    raise AssertionError(f"tampered OML-014 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-014 TEST")
    print(" STORE ADMISSION AND ATOMICITY CERTIFICATION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    store_contract = build_oml_013_contract(root)

    certification = (
        build_oracle_memory_store_admission_atomicity_certification(
            store_contract=store_contract,
        )
    )

    assert certification.schema_version == "OML-014"
    assert certification.engine_id == "OML-014"
    assert certification.upstream_schema_version == "OML-013"
    assert certification.upstream_engine_id == "OML-013"
    assert certification.upstream_certification_hash == (
        store_contract.certification_hash
    )
    assert certification.certified_domain_ids == MEMORY_DOMAINS
    assert certification.partition_count == 8
    assert certification.admission_status == "certified"
    assert (
        certification.atomicity_status
        == "single_commit_atomicity_certified"
    )
    assert certification.append_only_admitted
    assert certification.deterministic_commit_hashing_admitted
    assert certification.immutable_ledger_admitted
    assert certification.atomic_single_commit_admitted
    assert certification.full_replay_admitted
    assert certification.lineage_preservation_admitted
    assert certification.duplicate_record_rejection_admitted
    assert certification.destructive_updates_rejected
    assert certification.deletes_rejected
    assert certification.rollback_on_failure_required
    assert certification.partial_commit_forbidden
    assert certification.commit_order_canonical
    assert not certification.persistence_enabled
    assert not certification.learning_updates_enabled
    assert not certification.runtime_activation_enabled
    assert not certification.database_access_enabled
    assert not certification.networking_enabled
    assert not certification.publication_enabled
    assert not certification.action_authorization_enabled
    assert not certification.qseries_execution_enabled
    assert certification.certification_ready
    assert certification.next_certification_authorized
    assert certification.read_only

    replay = build_oracle_memory_store_admission_atomicity_certification(
        store_contract=store_contract,
    )

    assert replay == certification
    assert verify_oracle_memory_store_admission_atomicity_certification(
        certification
    )

    expect_rejection(
        lambda: verify_oracle_memory_store_admission_atomicity_certification(
            replace(certification, atomic_single_commit_admitted=False)
        ),
        "atomicity guarantee",
    )

    expect_rejection(
        lambda: verify_oracle_memory_store_admission_atomicity_certification(
            replace(certification, partial_commit_forbidden=False)
        ),
        "partial commit boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_store_admission_atomicity_certification(
            replace(certification, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_store_admission_atomicity_certification(
            replace(certification, qseries_execution_enabled=True)
        ),
        "Q Series execution boundary",
    )

    print("[PASS] Certified OML-013 store contract consumed")
    print("[PASS] OML-013 through OIT-050 lineage retained")
    print("[PASS] Eight store partitions admitted")
    print("[PASS] Append-only store architecture admitted")
    print("[PASS] Deterministic commit hashing admitted")
    print("[PASS] Atomic single-commit model certified")
    print("[PASS] Rollback on failure required")
    print("[PASS] Partial commits forbidden")
    print("[PASS] Full-ledger replay admitted")
    print("[PASS] Immutable lineage admitted")
    print("[PASS] Destructive updates and deletes rejected")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Database and networking remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Certification deterministic across replay")
    print("[PASS] Tampered certifications rejected")
    print("[DONE] OML-014 STORE ADMISSION AND ATOMICITY CERTIFICATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_actual_oml_013() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    module = importlib.import_module(
        "qseries_v2.oracle_memory.oracle_memory_store_contract"
    )

    expected = {
        "SCHEMA_VERSION": "OML-013",
        "ENGINE_ID": "OML-013",
        "POLICY_ID": "oracle-memory.store-contract.v1",
        "UPSTREAM_SCHEMA_VERSION": "OML-012",
        "UPSTREAM_ENGINE_ID": "OML-012",
        "STORE_MODE_APPEND_ONLY": "append_only",
        "STORE_STATE_CONTRACT_ONLY": "contract_only",
        "ATOMICITY_MODEL_SINGLE_COMMIT": "single_commit",
        "REPLAY_MODEL_FULL_LEDGER_REPLAY": "full_ledger_replay",
    }

    for name, value in expected.items():
        actual = getattr(module, name, None)

        if actual != value:
            raise RuntimeError(
                f"Certified OML-013 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    required = (
        "OracleMemoryStorePartitionContract",
        "OracleMemoryStoreContractCertification",
        "build_oracle_memory_store_contract_certification",
        "verify_oracle_memory_store_partition_contract",
        "verify_oracle_memory_store_contract_certification",
    )

    missing = [name for name in required if not hasattr(module, name)]

    if missing:
        raise RuntimeError(
            "Certified OML-013 missing required symbols: "
            + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-014 FOR-SURE INSTALLER")
    print(" STORE ADMISSION AND ATOMICITY CERTIFICATION")
    print("=" * 48)
    print("[BOOT] Revision: CAPABILITY_MILESTONE_FULL_REPLACEMENT")

    try:
        validate_actual_oml_013()
        print("[OK] Actual OML-013 imported and structurally verified")

        upstream = subprocess.run(
            [sys.executable, str(OML_013_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream.returncode:
            raise RuntimeError(
                "OML-013 certification failed with exit code "
                f"{upstream.returncode}"
            )

        production_before = OML_013.read_bytes()
        test_before = OML_013_TEST.read_bytes()

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_store_admission_and_atomicity_certification "
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
                "OML-014 test failed with exit code "
                f"{completed.returncode}"
            )

        if OML_013.read_bytes() != production_before:
            raise RuntimeError("Certified OML-013 production changed")

        if OML_013_TEST.read_bytes() != test_before:
            raise RuntimeError("Certified OML-013 standalone test changed")

        print("[PASS] Certified OML-013 production unchanged")
        print("[PASS] Certified OML-013 standalone test unchanged")
        print("[PASS] OML-014 store admission certification installed")
        print("[PASS] OML-014 standalone deterministic test installed")
        print("[PASS] Append-only store architecture admitted")
        print("[PASS] Atomic single-commit model certified")
        print("[PASS] Rollback and replay guarantees certified")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Database and networking remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OML-014 STORE ADMISSION AND "
            "ATOMICITY CERTIFICATION INSTALLED"
        )
        return 0

    except (RuntimeError, SyntaxError, ImportError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
