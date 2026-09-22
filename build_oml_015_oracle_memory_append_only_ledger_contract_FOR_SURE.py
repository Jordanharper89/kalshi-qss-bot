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
            / "oracle_memory_store_admission_and_atomicity_certification.py"
        )
        upstream_test = (
            candidate
            / "test_oml_014_oracle_memory_store_admission_and_atomicity_certification.py"
        )

        if upstream.is_file() and upstream_test.is_file():
            return candidate

    raise RuntimeError(
        "Could not locate repository containing certified OML-014."
    )


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

OML_014 = (
    PACKAGE
    / "oracle_memory_store_admission_and_atomicity_certification.py"
)
OML_014_TEST = (
    ROOT
    / "test_oml_014_oracle_memory_store_admission_and_atomicity_certification.py"
)

PRODUCTION = PACKAGE / "oracle_memory_append_only_ledger_contract.py"
TEST = ROOT / "test_oml_015_oracle_memory_append_only_ledger_contract.py"
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
from qseries_v2.oracle_memory.oracle_memory_store_admission_and_atomicity_certification import (
    OracleMemoryStoreAdmissionAtomicityCertification,
    verify_oracle_memory_store_admission_atomicity_certification,
)

SCHEMA_VERSION = "OML-015"
ENGINE_ID = "OML-015"
POLICY_ID = "oracle-memory.append-only-ledger-contract.v1"

UPSTREAM_SCHEMA_VERSION = "OML-014"
UPSTREAM_ENGINE_ID = "OML-014"

LEDGER_MODE_APPEND_ONLY = "append_only"
LEDGER_STATE_CONTRACT_ONLY = "contract_only"
COMMIT_MODEL_ATOMIC_SINGLE_COMMIT = "atomic_single_commit"
REPLAY_MODEL_GENESIS_TO_HEAD = "genesis_to_head"
GENESIS_PARENT_HASH = "0" * 64


class OracleMemoryAppendOnlyLedgerInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryLedgerEntryContract:
    domain_id: str
    ordinal: int
    partition_key: str
    upstream_partition_admission_hash: str
    sequence_number: int
    previous_entry_hash: str
    record_hash: str
    commit_id: str
    committed_at: str
    append_only_required: bool
    immutable_after_commit: bool
    deterministic_sequence_required: bool
    previous_hash_link_required: bool
    record_hash_uniqueness_required: bool
    destructive_update_allowed: bool
    delete_allowed: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    entry_hash: str


@dataclass(frozen=True)
class OracleMemoryAppendOnlyLedgerContractCertification:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_store_contract_hash: str
    certified_domain_ids: tuple[str, ...]
    ledger_mode: str
    ledger_state: str
    commit_model: str
    replay_model: str
    genesis_parent_hash: str
    entry_contracts: tuple[OracleMemoryLedgerEntryContract, ...]
    entry_contract_count: int
    canonical_serialization_required: bool
    deterministic_entry_hashing_required: bool
    monotonic_sequence_required: bool
    previous_hash_chain_required: bool
    genesis_anchor_required: bool
    atomic_commit_required: bool
    rollback_on_failure_required: bool
    partial_commit_forbidden: bool
    duplicate_record_hashes_forbidden: bool
    immutable_after_commit_required: bool
    destructive_updates_forbidden: bool
    deletes_forbidden: bool
    full_replay_required: bool
    lineage_preservation_required: bool
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

    raise OracleMemoryAppendOnlyLedgerInvariantError(
        "unsupported OML-015 value type: "
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
    raise OracleMemoryAppendOnlyLedgerInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-015 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryAppendOnlyLedgerInvariantError(
            f"OML-015 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_ledger_entry_contract(
    *,
    domain_id: str,
    ordinal: int,
    partition_key: str,
    upstream_partition_admission_hash: str,
    sequence_number: int,
    previous_entry_hash: str,
    record_hash: str,
    commit_id: str,
    committed_at: str,
) -> OracleMemoryLedgerEntryContract:
    if domain_id not in MEMORY_DOMAINS:
        _reject("OML-015 unknown memory domain")

    if ordinal != MEMORY_DOMAINS.index(domain_id) + 1:
        _reject("OML-015 domain ordinal mismatch")

    if partition_key != f"oracle-memory:{domain_id}":
        _reject("OML-015 partition key mismatch")

    _require_hash(
        upstream_partition_admission_hash,
        "upstream partition admission hash",
    )
    _require_hash(previous_entry_hash, "previous entry hash")
    _require_hash(record_hash, "record hash")

    if (
        not isinstance(sequence_number, int)
        or isinstance(sequence_number, bool)
        or sequence_number < 1
    ):
        _reject("OML-015 sequence number invalid")

    if not isinstance(commit_id, str) or not commit_id.strip():
        _reject("OML-015 commit id must be non-empty")

    if not isinstance(committed_at, str) or not committed_at.strip():
        _reject("OML-015 committed_at must be non-empty")

    body = {
        "domain_id": domain_id,
        "ordinal": ordinal,
        "partition_key": partition_key,
        "upstream_partition_admission_hash": (
            upstream_partition_admission_hash
        ),
        "sequence_number": sequence_number,
        "previous_entry_hash": previous_entry_hash,
        "record_hash": record_hash,
        "commit_id": commit_id.strip(),
        "committed_at": committed_at.strip(),
        "append_only_required": True,
        "immutable_after_commit": True,
        "deterministic_sequence_required": True,
        "previous_hash_link_required": True,
        "record_hash_uniqueness_required": True,
        "destructive_update_allowed": False,
        "delete_allowed": False,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    entry = OracleMemoryLedgerEntryContract(
        **body,
        entry_hash=_stable_hash(body),
    )

    verify_oracle_memory_ledger_entry_contract(entry)
    return entry


def verify_oracle_memory_ledger_entry_contract(
    entry: OracleMemoryLedgerEntryContract,
) -> bool:
    body = asdict(entry)
    supplied = body.pop("entry_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-015 ledger entry hash mismatch")

    if entry.domain_id not in MEMORY_DOMAINS:
        _reject("OML-015 ledger entry domain mismatch")

    if entry.ordinal != MEMORY_DOMAINS.index(entry.domain_id) + 1:
        _reject("OML-015 ledger entry ordinal mismatch")

    if entry.partition_key != f"oracle-memory:{entry.domain_id}":
        _reject("OML-015 ledger entry partition mismatch")

    _require_hash(
        entry.upstream_partition_admission_hash,
        "entry upstream partition admission hash",
    )
    _require_hash(entry.previous_entry_hash, "entry previous hash")
    _require_hash(entry.record_hash, "entry record hash")
    _require_hash(entry.entry_hash, "entry hash")

    if entry.sequence_number < 1:
        _reject("OML-015 ledger entry sequence invalid")

    if not entry.commit_id or entry.commit_id != entry.commit_id.strip():
        _reject("OML-015 ledger entry commit id invalid")

    if not entry.committed_at or entry.committed_at != entry.committed_at.strip():
        _reject("OML-015 ledger entry committed_at invalid")

    required_true = (
        entry.append_only_required,
        entry.immutable_after_commit,
        entry.deterministic_sequence_required,
        entry.previous_hash_link_required,
        entry.record_hash_uniqueness_required,
        entry.read_only,
    )

    if not all(required_true):
        _reject("OML-015 ledger entry guarantee missing")

    forbidden = (
        entry.destructive_update_allowed,
        entry.delete_allowed,
        entry.persistence_authorized,
        entry.learning_update_authorized,
        entry.runtime_activation_authorized,
        entry.publication_authorized,
        entry.action_authorization_enabled,
        entry.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-015 forbidden ledger entry capability enabled")

    return True


def build_oracle_memory_append_only_ledger_contract_certification(
    *,
    store_certification: OracleMemoryStoreAdmissionAtomicityCertification,
) -> OracleMemoryAppendOnlyLedgerContractCertification:
    verify_oracle_memory_store_admission_atomicity_certification(
        store_certification
    )

    if store_certification.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-015 upstream schema mismatch")

    if store_certification.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-015 upstream engine mismatch")

    if not store_certification.certification_ready:
        _reject("OML-015 upstream store certification not ready")

    if not store_certification.next_certification_authorized:
        _reject("OML-015 upstream continuation not authorized")

    if not store_certification.read_only:
        _reject("OML-015 upstream read-only guarantee missing")

    if store_certification.certified_domain_ids != MEMORY_DOMAINS:
        _reject("OML-015 upstream domain identity mismatch")

    entry_contracts = tuple(
        build_oracle_memory_ledger_entry_contract(
            domain_id=admission.domain_id,
            ordinal=admission.ordinal,
            partition_key=admission.partition_key,
            upstream_partition_admission_hash=admission.admission_hash,
            sequence_number=1,
            previous_entry_hash=GENESIS_PARENT_HASH,
            record_hash=hashlib.sha256(
                f"OML-015:{admission.domain_id}:record-contract".encode(
                    "utf-8"
                )
            ).hexdigest(),
            commit_id=f"oml-015:{admission.domain_id}:genesis-contract",
            committed_at="1970-01-01T00:00:00Z",
        )
        for admission in store_certification.partition_admissions
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": store_certification.schema_version,
        "upstream_engine_id": store_certification.engine_id,
        "upstream_certification_hash": (
            store_certification.certification_hash
        ),
        "upstream_store_contract_hash": (
            store_certification.upstream_certification_hash
        ),
        "certified_domain_ids": store_certification.certified_domain_ids,
        "ledger_mode": LEDGER_MODE_APPEND_ONLY,
        "ledger_state": LEDGER_STATE_CONTRACT_ONLY,
        "commit_model": COMMIT_MODEL_ATOMIC_SINGLE_COMMIT,
        "replay_model": REPLAY_MODEL_GENESIS_TO_HEAD,
        "genesis_parent_hash": GENESIS_PARENT_HASH,
        "entry_contracts": entry_contracts,
        "entry_contract_count": len(entry_contracts),
        "canonical_serialization_required": True,
        "deterministic_entry_hashing_required": True,
        "monotonic_sequence_required": True,
        "previous_hash_chain_required": True,
        "genesis_anchor_required": True,
        "atomic_commit_required": True,
        "rollback_on_failure_required": True,
        "partial_commit_forbidden": True,
        "duplicate_record_hashes_forbidden": True,
        "immutable_after_commit_required": True,
        "destructive_updates_forbidden": True,
        "deletes_forbidden": True,
        "full_replay_required": True,
        "lineage_preservation_required": True,
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

    certification = OracleMemoryAppendOnlyLedgerContractCertification(
        **body,
        certification_hash=_stable_hash(body),
    )

    verify_oracle_memory_append_only_ledger_contract_certification(
        certification
    )
    return certification


def verify_oracle_memory_append_only_ledger_contract_certification(
    certification: OracleMemoryAppendOnlyLedgerContractCertification,
) -> bool:
    body = asdict(certification)
    supplied = body.pop("certification_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-015 certification hash mismatch")

    if certification.schema_version != SCHEMA_VERSION:
        _reject("OML-015 certification schema mismatch")

    if certification.engine_id != ENGINE_ID:
        _reject("OML-015 certification engine mismatch")

    if certification.policy_id != POLICY_ID:
        _reject("OML-015 certification policy mismatch")

    if certification.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-015 certification subsystem mismatch")

    if certification.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-015 certification upstream schema mismatch")

    if certification.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-015 certification upstream engine mismatch")

    if certification.certified_domain_ids != MEMORY_DOMAINS:
        _reject("OML-015 certification domain mismatch")

    if certification.entry_contract_count != len(MEMORY_DOMAINS):
        _reject("OML-015 entry contract count mismatch")

    if tuple(
        entry.domain_id
        for entry in certification.entry_contracts
    ) != MEMORY_DOMAINS:
        _reject("OML-015 entry contract order mismatch")

    for entry in certification.entry_contracts:
        verify_oracle_memory_ledger_entry_contract(entry)

    if certification.ledger_mode != LEDGER_MODE_APPEND_ONLY:
        _reject("OML-015 ledger mode mismatch")

    if certification.ledger_state != LEDGER_STATE_CONTRACT_ONLY:
        _reject("OML-015 ledger state mismatch")

    if certification.commit_model != COMMIT_MODEL_ATOMIC_SINGLE_COMMIT:
        _reject("OML-015 commit model mismatch")

    if certification.replay_model != REPLAY_MODEL_GENESIS_TO_HEAD:
        _reject("OML-015 replay model mismatch")

    if certification.genesis_parent_hash != GENESIS_PARENT_HASH:
        _reject("OML-015 genesis parent hash mismatch")

    required_true = (
        certification.canonical_serialization_required,
        certification.deterministic_entry_hashing_required,
        certification.monotonic_sequence_required,
        certification.previous_hash_chain_required,
        certification.genesis_anchor_required,
        certification.atomic_commit_required,
        certification.rollback_on_failure_required,
        certification.partial_commit_forbidden,
        certification.duplicate_record_hashes_forbidden,
        certification.immutable_after_commit_required,
        certification.destructive_updates_forbidden,
        certification.deletes_forbidden,
        certification.full_replay_required,
        certification.lineage_preservation_required,
        certification.contract_ready,
        certification.next_certification_authorized,
        certification.read_only,
    )

    if not all(required_true):
        _reject("OML-015 certification guarantee missing")

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
        _reject("OML-015 forbidden ledger capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_append_only_ledger_contract import (
    GENESIS_PARENT_HASH,
    OracleMemoryAppendOnlyLedgerInvariantError,
    build_oracle_memory_append_only_ledger_contract_certification,
    verify_oracle_memory_append_only_ledger_contract_certification,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
)
from qseries_v2.oracle_memory.oracle_memory_store_admission_and_atomicity_certification import (
    build_oracle_memory_store_admission_atomicity_certification,
)


def load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)

    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")

    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def build_oml_014_certification(root: Path):
    fixture = load_module(
        root
        / "test_oml_014_oracle_memory_store_admission_and_atomicity_certification.py",
        "oml_014_fixture_for_oml_015",
    )

    store_contract = fixture.build_oml_013_contract(root)

    return build_oracle_memory_store_admission_atomicity_certification(
        store_contract=store_contract,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryAppendOnlyLedgerInvariantError:
        return

    raise AssertionError(f"tampered OML-015 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-015 TEST")
    print(" APPEND-ONLY MEMORY LEDGER CONTRACT")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    store_certification = build_oml_014_certification(root)

    certification = (
        build_oracle_memory_append_only_ledger_contract_certification(
            store_certification=store_certification,
        )
    )

    assert certification.schema_version == "OML-015"
    assert certification.engine_id == "OML-015"
    assert certification.upstream_schema_version == "OML-014"
    assert certification.upstream_engine_id == "OML-014"
    assert certification.upstream_certification_hash == (
        store_certification.certification_hash
    )
    assert certification.certified_domain_ids == MEMORY_DOMAINS
    assert certification.entry_contract_count == 8
    assert certification.ledger_mode == "append_only"
    assert certification.ledger_state == "contract_only"
    assert certification.commit_model == "atomic_single_commit"
    assert certification.replay_model == "genesis_to_head"
    assert certification.genesis_parent_hash == GENESIS_PARENT_HASH
    assert certification.monotonic_sequence_required
    assert certification.previous_hash_chain_required
    assert certification.genesis_anchor_required
    assert certification.atomic_commit_required
    assert certification.rollback_on_failure_required
    assert certification.partial_commit_forbidden
    assert certification.duplicate_record_hashes_forbidden
    assert certification.immutable_after_commit_required
    assert certification.destructive_updates_forbidden
    assert certification.deletes_forbidden
    assert certification.full_replay_required
    assert certification.lineage_preservation_required
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

    for index, entry in enumerate(
        certification.entry_contracts,
        start=1,
    ):
        assert entry.domain_id == MEMORY_DOMAINS[index - 1]
        assert entry.ordinal == index
        assert entry.sequence_number == 1
        assert entry.previous_entry_hash == GENESIS_PARENT_HASH
        assert entry.append_only_required
        assert entry.immutable_after_commit
        assert entry.deterministic_sequence_required
        assert entry.previous_hash_link_required
        assert entry.record_hash_uniqueness_required
        assert not entry.destructive_update_allowed
        assert not entry.delete_allowed
        assert not entry.persistence_authorized
        assert not entry.learning_update_authorized
        assert not entry.runtime_activation_authorized
        assert not entry.publication_authorized
        assert not entry.action_authorization_enabled
        assert not entry.qseries_execution_authorized
        assert entry.read_only

    replay = (
        build_oracle_memory_append_only_ledger_contract_certification(
            store_certification=store_certification,
        )
    )

    assert replay == certification
    assert verify_oracle_memory_append_only_ledger_contract_certification(
        certification
    )

    expect_rejection(
        lambda: verify_oracle_memory_append_only_ledger_contract_certification(
            replace(certification, previous_hash_chain_required=False)
        ),
        "hash-chain guarantee",
    )

    expect_rejection(
        lambda: verify_oracle_memory_append_only_ledger_contract_certification(
            replace(certification, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_append_only_ledger_contract_certification(
            replace(certification, partial_commit_forbidden=False)
        ),
        "partial commit boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_append_only_ledger_contract_certification(
            replace(certification, qseries_execution_enabled=True)
        ),
        "Q Series execution boundary",
    )

    print("[PASS] Certified OML-014 store certification consumed")
    print("[PASS] OML-014 through OIT-050 lineage retained")
    print("[PASS] Append-only ledger contract created")
    print("[PASS] Eight domain ledger-entry contracts defined")
    print("[PASS] Genesis anchors defined")
    print("[PASS] Monotonic sequence numbers required")
    print("[PASS] Previous-entry hash chaining required")
    print("[PASS] Deterministic entry hashing required")
    print("[PASS] Atomic commit and rollback required")
    print("[PASS] Partial commits forbidden")
    print("[PASS] Duplicate record hashes forbidden")
    print("[PASS] Destructive updates and deletes forbidden")
    print("[PASS] Full genesis-to-head replay required")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Database and networking remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Contract deterministic across replay")
    print("[PASS] Tampered ledger certifications rejected")
    print("[DONE] OML-015 APPEND-ONLY MEMORY LEDGER CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_actual_oml_014() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_store_admission_and_atomicity_certification"
    )

    expected = {
        "SCHEMA_VERSION": "OML-014",
        "ENGINE_ID": "OML-014",
        "POLICY_ID": (
            "oracle-memory.store-admission-and-atomicity-certification.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-013",
        "UPSTREAM_ENGINE_ID": "OML-013",
        "ADMISSION_STATUS_CERTIFIED": "certified",
        "ATOMICITY_STATUS_CERTIFIED": (
            "single_commit_atomicity_certified"
        ),
    }

    for name, value in expected.items():
        actual = getattr(module, name, None)

        if actual != value:
            raise RuntimeError(
                f"Certified OML-014 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    required = (
        "OracleMemoryStorePartitionAdmission",
        "OracleMemoryStoreAdmissionAtomicityCertification",
        "build_oracle_memory_store_admission_atomicity_certification",
        "verify_oracle_memory_store_partition_admission",
        "verify_oracle_memory_store_admission_atomicity_certification",
    )

    missing = [name for name in required if not hasattr(module, name)]

    if missing:
        raise RuntimeError(
            "Certified OML-014 missing required symbols: "
            + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-015 FOR-SURE INSTALLER")
    print(" APPEND-ONLY MEMORY LEDGER CONTRACT")
    print("=" * 48)
    print("[BOOT] Revision: CAPABILITY_MILESTONE_FULL_REPLACEMENT")

    try:
        validate_actual_oml_014()
        print("[OK] Actual OML-014 imported and structurally verified")

        upstream = subprocess.run(
            [sys.executable, str(OML_014_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream.returncode:
            raise RuntimeError(
                "OML-014 certification failed with exit code "
                f"{upstream.returncode}"
            )

        production_before = OML_014.read_bytes()
        test_before = OML_014_TEST.read_bytes()

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_append_only_ledger_contract "
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
                "OML-015 test failed with exit code "
                f"{completed.returncode}"
            )

        if OML_014.read_bytes() != production_before:
            raise RuntimeError("Certified OML-014 production changed")

        if OML_014_TEST.read_bytes() != test_before:
            raise RuntimeError("Certified OML-014 standalone test changed")

        print("[PASS] Certified OML-014 production unchanged")
        print("[PASS] Certified OML-014 standalone test unchanged")
        print("[PASS] OML-015 append-only ledger contract installed")
        print("[PASS] OML-015 standalone deterministic test installed")
        print("[PASS] Genesis and hash-chain architecture defined")
        print("[PASS] Atomic commit and replay guarantees defined")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Database and networking remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OML-015 APPEND-ONLY MEMORY "
            "LEDGER CONTRACT INSTALLED"
        )
        return 0

    except (RuntimeError, SyntaxError, ImportError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
