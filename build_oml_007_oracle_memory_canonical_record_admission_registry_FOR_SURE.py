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
            / "oracle_memory_canonical_record_contract_admission_gate.py"
        )
        upstream_test = (
            candidate
            / "test_oml_006_oracle_memory_canonical_record_contract_admission_gate.py"
        )

        if upstream.is_file() and upstream_test.is_file():
            return candidate

    raise RuntimeError(
        "Could not locate repository containing certified OML-006."
    )


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

OML_006 = (
    PACKAGE
    / "oracle_memory_canonical_record_contract_admission_gate.py"
)
OML_006_TEST = (
    ROOT
    / "test_oml_006_oracle_memory_canonical_record_contract_admission_gate.py"
)

PRODUCTION = PACKAGE / "oracle_memory_canonical_record_admission_registry.py"
TEST = ROOT / "test_oml_007_oracle_memory_canonical_record_admission_registry.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_canonical_record_contract_admission_gate import (
    OracleMemoryCanonicalRecordContractAdmissionDecision,
    verify_oracle_memory_canonical_record_contract_admission_decision,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-007"
ENGINE_ID = "OML-007"
POLICY_ID = "oracle-memory.canonical-record-admission-registry.v1"

UPSTREAM_SCHEMA_VERSION = "OML-006"
UPSTREAM_ENGINE_ID = "OML-006"
REGISTRY_STATUS_CERTIFIED = "certified_inactive"


class OracleMemoryCanonicalRecordAdmissionRegistryInvariantError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class OracleMemoryCanonicalRecordAdmissionEntry:
    domain_id: str
    ordinal: int
    upstream_contract_admission_hash: str
    canonical_record_contract_admitted: bool
    persistent_storage_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    entry_hash: str


@dataclass(frozen=True)
class OracleMemoryCanonicalRecordAdmissionRegistry:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_decision_hash: str
    upstream_certification_hash: str
    upstream_admission_hash: str
    upstream_registry_hash: str
    registry_status: str
    entries: tuple[OracleMemoryCanonicalRecordAdmissionEntry, ...]
    entry_count: int
    domain_order_canonical: bool
    identities_unique: bool
    all_contracts_admitted: bool
    all_entries_inactive: bool
    all_entries_non_writing: bool
    all_entries_read_only: bool
    publication_disabled: bool
    action_authorization_disabled: bool
    qseries_execution_disabled: bool
    next_certification_authorized: bool
    registry_hash: str


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

    raise OracleMemoryCanonicalRecordAdmissionRegistryInvariantError(
        "unsupported OML-007 value type: "
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
    raise OracleMemoryCanonicalRecordAdmissionRegistryInvariantError(
        reason
    )


def _build_entry(
    *,
    domain_id: str,
    ordinal: int,
    upstream_contract_admission_hash: str,
) -> OracleMemoryCanonicalRecordAdmissionEntry:
    body = {
        "domain_id": domain_id,
        "ordinal": ordinal,
        "upstream_contract_admission_hash": (
            upstream_contract_admission_hash
        ),
        "canonical_record_contract_admitted": True,
        "persistent_storage_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    return OracleMemoryCanonicalRecordAdmissionEntry(
        **body,
        entry_hash=_stable_hash(body),
    )


def verify_oracle_memory_canonical_record_admission_entry(
    entry: OracleMemoryCanonicalRecordAdmissionEntry,
) -> bool:
    body = asdict(entry)
    supplied = body.pop("entry_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-007 admission entry hash mismatch")

    if entry.domain_id not in MEMORY_DOMAINS:
        _reject("OML-007 unknown memory domain")

    if entry.ordinal != MEMORY_DOMAINS.index(entry.domain_id) + 1:
        _reject("OML-007 domain ordinal mismatch")

    if len(entry.upstream_contract_admission_hash) != 64:
        _reject("OML-007 upstream admission hash invalid")

    if not entry.canonical_record_contract_admitted:
        _reject("OML-007 record contract not admitted")

    forbidden = (
        entry.persistent_storage_authorized,
        entry.learning_update_authorized,
        entry.runtime_activation_authorized,
        entry.publication_authorized,
        entry.action_authorization_enabled,
        entry.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-007 forbidden entry capability enabled")

    if not entry.read_only:
        _reject("OML-007 entry is not read-only")

    return True


def build_oracle_memory_canonical_record_admission_registry(
    *,
    admission_decision: OracleMemoryCanonicalRecordContractAdmissionDecision,
) -> OracleMemoryCanonicalRecordAdmissionRegistry:
    verify_oracle_memory_canonical_record_contract_admission_decision(
        admission_decision
    )

    if admission_decision.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-007 upstream schema mismatch")

    if admission_decision.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-007 upstream engine mismatch")

    if not admission_decision.admitted:
        _reject("OML-007 upstream contract not admitted")

    if not admission_decision.next_certification_authorized:
        _reject("OML-007 upstream continuation not authorized")

    if not admission_decision.read_only:
        _reject("OML-007 upstream read-only guarantee missing")

    if admission_decision.certified_domain_ids != MEMORY_DOMAINS:
        _reject("OML-007 upstream domain identity mismatch")

    entries = tuple(
        _build_entry(
            domain_id=domain_id,
            ordinal=index,
            upstream_contract_admission_hash=(
                admission_decision.decision_hash
            ),
        )
        for index, domain_id in enumerate(MEMORY_DOMAINS, start=1)
    )

    for entry in entries:
        verify_oracle_memory_canonical_record_admission_entry(entry)

    domain_ids = tuple(entry.domain_id for entry in entries)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": admission_decision.schema_version,
        "upstream_engine_id": admission_decision.engine_id,
        "upstream_decision_hash": admission_decision.decision_hash,
        "upstream_certification_hash": (
            admission_decision.upstream_certification_hash
        ),
        "upstream_admission_hash": (
            admission_decision.upstream_admission_hash
        ),
        "upstream_registry_hash": (
            admission_decision.upstream_registry_hash
        ),
        "registry_status": REGISTRY_STATUS_CERTIFIED,
        "entries": entries,
        "entry_count": len(entries),
        "domain_order_canonical": domain_ids == MEMORY_DOMAINS,
        "identities_unique": len(set(domain_ids)) == len(domain_ids),
        "all_contracts_admitted": all(
            entry.canonical_record_contract_admitted
            for entry in entries
        ),
        "all_entries_inactive": all(
            not entry.runtime_activation_authorized
            for entry in entries
        ),
        "all_entries_non_writing": all(
            not entry.persistent_storage_authorized
            and not entry.learning_update_authorized
            for entry in entries
        ),
        "all_entries_read_only": all(
            entry.read_only
            for entry in entries
        ),
        "publication_disabled": all(
            not entry.publication_authorized
            for entry in entries
        ),
        "action_authorization_disabled": all(
            not entry.action_authorization_enabled
            for entry in entries
        ),
        "qseries_execution_disabled": all(
            not entry.qseries_execution_authorized
            for entry in entries
        ),
        "next_certification_authorized": True,
    }

    registry = OracleMemoryCanonicalRecordAdmissionRegistry(
        **body,
        registry_hash=_stable_hash(body),
    )

    verify_oracle_memory_canonical_record_admission_registry(registry)
    return registry


def verify_oracle_memory_canonical_record_admission_registry(
    registry: OracleMemoryCanonicalRecordAdmissionRegistry,
) -> bool:
    body = asdict(registry)
    supplied = body.pop("registry_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-007 registry hash mismatch")

    if registry.schema_version != SCHEMA_VERSION:
        _reject("OML-007 schema mismatch")

    if registry.engine_id != ENGINE_ID:
        _reject("OML-007 engine mismatch")

    if registry.policy_id != POLICY_ID:
        _reject("OML-007 policy mismatch")

    if registry.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-007 subsystem mismatch")

    if registry.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-007 upstream schema lineage mismatch")

    if registry.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-007 upstream engine lineage mismatch")

    hashes = (
        registry.upstream_decision_hash,
        registry.upstream_certification_hash,
        registry.upstream_admission_hash,
        registry.upstream_registry_hash,
        registry.registry_hash,
    )

    if any(len(value) != 64 for value in hashes):
        _reject("OML-007 lineage hash length invalid")

    if registry.registry_status != REGISTRY_STATUS_CERTIFIED:
        _reject("OML-007 registry status mismatch")

    if registry.entry_count != len(MEMORY_DOMAINS):
        _reject("OML-007 registry entry count mismatch")

    if tuple(entry.domain_id for entry in registry.entries) != MEMORY_DOMAINS:
        _reject("OML-007 registry domain order mismatch")

    for entry in registry.entries:
        verify_oracle_memory_canonical_record_admission_entry(entry)

    required_true = (
        registry.domain_order_canonical,
        registry.identities_unique,
        registry.all_contracts_admitted,
        registry.all_entries_inactive,
        registry.all_entries_non_writing,
        registry.all_entries_read_only,
        registry.publication_disabled,
        registry.action_authorization_disabled,
        registry.qseries_execution_disabled,
        registry.next_certification_authorized,
    )

    if not all(required_true):
        _reject("OML-007 registry guarantee missing")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_canonical_record_admission_registry import (
    REGISTRY_STATUS_CERTIFIED,
    OracleMemoryCanonicalRecordAdmissionRegistryInvariantError,
    build_oracle_memory_canonical_record_admission_registry,
    verify_oracle_memory_canonical_record_admission_registry,
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


def load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)

    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")

    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def build_oml_006_decision(root: Path):
    fixture = load_module(
        root
        / "test_oit_050_oracle_terminal_final_freeze_and_completion.py",
        "oit_050_fixture_for_oml_007",
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

    return build_oracle_memory_canonical_record_contract_admission_decision(
        certification=oml_005,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryCanonicalRecordAdmissionRegistryInvariantError:
        return

    raise AssertionError(f"tampered OML-007 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-007 TEST")
    print(" CANONICAL RECORD ADMISSION REGISTRY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    admission = build_oml_006_decision(root)

    registry = build_oracle_memory_canonical_record_admission_registry(
        admission_decision=admission,
    )

    assert registry.schema_version == "OML-007"
    assert registry.engine_id == "OML-007"
    assert registry.upstream_schema_version == "OML-006"
    assert registry.upstream_engine_id == "OML-006"
    assert registry.upstream_decision_hash == admission.decision_hash
    assert registry.entry_count == 8
    assert tuple(entry.domain_id for entry in registry.entries) == (
        MEMORY_DOMAINS
    )
    assert registry.registry_status == REGISTRY_STATUS_CERTIFIED
    assert registry.domain_order_canonical
    assert registry.identities_unique
    assert registry.all_contracts_admitted
    assert registry.all_entries_inactive
    assert registry.all_entries_non_writing
    assert registry.all_entries_read_only
    assert registry.publication_disabled
    assert registry.action_authorization_disabled
    assert registry.qseries_execution_disabled
    assert registry.next_certification_authorized

    for index, entry in enumerate(registry.entries, start=1):
        assert entry.ordinal == index
        assert entry.domain_id == MEMORY_DOMAINS[index - 1]
        assert entry.upstream_contract_admission_hash == (
            admission.decision_hash
        )
        assert entry.canonical_record_contract_admitted
        assert not entry.persistent_storage_authorized
        assert not entry.learning_update_authorized
        assert not entry.runtime_activation_authorized
        assert not entry.publication_authorized
        assert not entry.action_authorization_enabled
        assert not entry.qseries_execution_authorized
        assert entry.read_only

    replay = build_oracle_memory_canonical_record_admission_registry(
        admission_decision=admission,
    )

    assert replay == registry
    assert verify_oracle_memory_canonical_record_admission_registry(
        registry
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_admission_registry(
            replace(registry, entry_count=7)
        ),
        "entry count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_admission_registry(
            replace(registry, all_entries_non_writing=False)
        ),
        "non-writing guarantee",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_admission_registry(
            replace(registry, publication_disabled=False)
        ),
        "publication boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_admission_registry(
            replace(registry, qseries_execution_disabled=False)
        ),
        "Q Series execution boundary",
    )

    print("[PASS] Certified OML-006 admission consumed")
    print("[PASS] OML-006 through OIT-050 lineage retained")
    print("[PASS] Eight canonical record admissions registered")
    print("[PASS] Domain identities unique and canonically ordered")
    print("[PASS] Every record contract remained admitted")
    print("[PASS] Every registry entry remained inactive")
    print("[PASS] Persistent storage remained unauthorized")
    print("[PASS] Learning updates remained unauthorized")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Registry deterministic across replay")
    print("[PASS] Tampered registry states rejected")
    print("[DONE] OML-007 CANONICAL RECORD ADMISSION REGISTRY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_actual_oml_006() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_canonical_record_contract_admission_gate"
    )

    expected = {
        "SCHEMA_VERSION": "OML-006",
        "ENGINE_ID": "OML-006",
        "POLICY_ID": (
            "oracle-memory.canonical-record-contract-admission-gate.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-005",
        "UPSTREAM_ENGINE_ID": "OML-005",
        "ADMISSION_STATUS_ADMITTED": "admitted",
    }

    for name, value in expected.items():
        actual = getattr(module, name, None)

        if actual != value:
            raise RuntimeError(
                f"Certified OML-006 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    required = (
        "OracleMemoryCanonicalRecordContractAdmissionDecision",
        "build_oracle_memory_canonical_record_contract_admission_decision",
        "verify_oracle_memory_canonical_record_contract_admission_decision",
    )

    missing = [name for name in required if not hasattr(module, name)]

    if missing:
        raise RuntimeError(
            "Certified OML-006 missing required symbols: "
            + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-007 FOR-SURE INSTALLER")
    print(" CANONICAL RECORD ADMISSION REGISTRY")
    print("=" * 48)
    print("[BOOT] Revision: IMPORT_ALIGNED_FULL_REPLACEMENT")

    try:
        validate_actual_oml_006()
        print("[OK] Actual OML-006 imported and structurally verified")

        upstream = subprocess.run(
            [sys.executable, str(OML_006_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream.returncode:
            raise RuntimeError(
                "OML-006 certification failed with exit code "
                f"{upstream.returncode}"
            )

        production_before = OML_006.read_bytes()
        test_before = OML_006_TEST.read_bytes()

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_canonical_record_admission_registry "
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
                "OML-007 test failed with exit code "
                f"{completed.returncode}"
            )

        if OML_006.read_bytes() != production_before:
            raise RuntimeError("Certified OML-006 production changed")

        if OML_006_TEST.read_bytes() != test_before:
            raise RuntimeError("Certified OML-006 standalone test changed")

        print("[PASS] Certified OML-006 production unchanged")
        print("[PASS] Certified OML-006 standalone test unchanged")
        print("[PASS] OML-007 admission registry installed")
        print("[PASS] OML-007 deterministic standalone test installed")
        print("[PASS] Eight canonical record admissions registered")
        print("[PASS] All entries remained inactive and non-writing")
        print("[PASS] Persistent memory remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OML-007 CANONICAL RECORD ADMISSION "
            "REGISTRY INSTALLED"
        )
        return 0

    except (RuntimeError, SyntaxError, ImportError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
