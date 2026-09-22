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
            / "oracle_memory_learner_foundation_admission_gate.py"
        )
        upstream_test = (
            candidate
            / "test_oml_002_oracle_memory_learner_foundation_admission_gate.py"
        )

        if upstream.is_file() and upstream_test.is_file():
            return candidate

    raise RuntimeError(
        "Could not locate repository containing certified OML-002."
    )


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

OML_002 = PACKAGE / "oracle_memory_learner_foundation_admission_gate.py"
OML_002_TEST = (
    ROOT
    / "test_oml_002_oracle_memory_learner_foundation_admission_gate.py"
)

PRODUCTION = PACKAGE / "oracle_memory_certified_domain_registry.py"
TEST = ROOT / "test_oml_003_oracle_memory_certified_domain_registry.py"
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
from qseries_v2.oracle_memory.oracle_memory_learner_foundation_admission_gate import (
    OracleMemoryLearnerFoundationAdmissionDecision,
    verify_oracle_memory_learner_foundation_admission_decision,
)

SCHEMA_VERSION = "OML-003"
ENGINE_ID = "OML-003"
POLICY_ID = "oracle-memory.certified-domain-registry.v1"

UPSTREAM_SCHEMA_VERSION = "OML-002"
UPSTREAM_ENGINE_ID = "OML-002"
REGISTRY_STATUS_CERTIFIED = "certified_inactive"
DOMAIN_KIND_MEMORY = "memory"


class OracleMemoryDomainRegistryInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryDomainDefinition:
    domain_id: str
    domain_kind: str
    ordinal: int
    persistent_storage_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    database_access_authorized: bool
    networking_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    definition_hash: str


@dataclass(frozen=True)
class OracleMemoryCertifiedDomainRegistry:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_decision_hash: str
    upstream_foundation_report_hash: str
    upstream_oit_report_hash: str
    upstream_oit_runner_sha256: str
    registry_status: str
    domains: tuple[OracleMemoryDomainDefinition, ...]
    domain_count: int
    registry_complete: bool
    domain_order_canonical: bool
    identities_unique: bool
    all_domains_inactive: bool
    all_domains_non_writing: bool
    all_domains_read_only: bool
    no_database_access_authorized: bool
    no_networking_authorized: bool
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

    raise OracleMemoryDomainRegistryInvariantError(
        "unsupported OML-003 value type: "
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
    raise OracleMemoryDomainRegistryInvariantError(reason)


def _build_domain(
    domain_id: str,
    ordinal: int,
) -> OracleMemoryDomainDefinition:
    body = {
        "domain_id": domain_id,
        "domain_kind": DOMAIN_KIND_MEMORY,
        "ordinal": ordinal,
        "persistent_storage_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "database_access_authorized": False,
        "networking_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    return OracleMemoryDomainDefinition(
        **body,
        definition_hash=_stable_hash(body),
    )


def verify_oracle_memory_domain_definition(
    definition: OracleMemoryDomainDefinition,
) -> bool:
    body = asdict(definition)
    supplied = body.pop("definition_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-003 domain definition hash mismatch")

    if definition.domain_id not in MEMORY_DOMAINS:
        _reject("OML-003 unknown memory domain")

    expected_ordinal = MEMORY_DOMAINS.index(definition.domain_id) + 1

    if definition.ordinal != expected_ordinal:
        _reject("OML-003 memory domain ordinal mismatch")

    if definition.domain_kind != DOMAIN_KIND_MEMORY:
        _reject("OML-003 memory domain kind mismatch")

    forbidden = (
        definition.persistent_storage_authorized,
        definition.learning_update_authorized,
        definition.runtime_activation_authorized,
        definition.database_access_authorized,
        definition.networking_authorized,
        definition.publication_authorized,
        definition.action_authorization_enabled,
        definition.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-003 forbidden domain capability enabled")

    if not definition.read_only:
        _reject("OML-003 memory domain is not read-only")

    return True


def build_oracle_memory_certified_domain_registry(
    *,
    admission_decision: OracleMemoryLearnerFoundationAdmissionDecision,
) -> OracleMemoryCertifiedDomainRegistry:
    verify_oracle_memory_learner_foundation_admission_decision(
        admission_decision
    )

    if admission_decision.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-003 upstream schema mismatch")

    if admission_decision.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-003 upstream engine mismatch")

    if not admission_decision.admitted:
        _reject("OML-003 upstream admission not granted")

    if not admission_decision.next_certification_authorized:
        _reject("OML-003 upstream continuation not authorized")

    if not admission_decision.read_only:
        _reject("OML-003 upstream read-only guarantee missing")

    if tuple(admission_decision.configured_memory_domains) != MEMORY_DOMAINS:
        _reject("OML-003 upstream memory-domain lineage mismatch")

    domains = tuple(
        _build_domain(domain_id, index)
        for index, domain_id in enumerate(MEMORY_DOMAINS, start=1)
    )

    for definition in domains:
        verify_oracle_memory_domain_definition(definition)

    domain_ids = tuple(item.domain_id for item in domains)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": admission_decision.schema_version,
        "upstream_engine_id": admission_decision.engine_id,
        "upstream_decision_hash": admission_decision.decision_hash,
        "upstream_foundation_report_hash": (
            admission_decision.upstream_report_hash
        ),
        "upstream_oit_report_hash": (
            admission_decision.upstream_oit_report_hash
        ),
        "upstream_oit_runner_sha256": (
            admission_decision.upstream_oit_runner_sha256
        ),
        "registry_status": REGISTRY_STATUS_CERTIFIED,
        "domains": domains,
        "domain_count": len(domains),
        "registry_complete": len(domains) == len(MEMORY_DOMAINS),
        "domain_order_canonical": domain_ids == MEMORY_DOMAINS,
        "identities_unique": len(set(domain_ids)) == len(domain_ids),
        "all_domains_inactive": all(
            not item.runtime_activation_authorized
            for item in domains
        ),
        "all_domains_non_writing": all(
            not item.persistent_storage_authorized
            and not item.learning_update_authorized
            for item in domains
        ),
        "all_domains_read_only": all(
            item.read_only
            for item in domains
        ),
        "no_database_access_authorized": all(
            not item.database_access_authorized
            for item in domains
        ),
        "no_networking_authorized": all(
            not item.networking_authorized
            for item in domains
        ),
        "publication_disabled": all(
            not item.publication_authorized
            for item in domains
        ),
        "action_authorization_disabled": all(
            not item.action_authorization_enabled
            for item in domains
        ),
        "qseries_execution_disabled": all(
            not item.qseries_execution_authorized
            for item in domains
        ),
        "next_certification_authorized": True,
    }

    registry = OracleMemoryCertifiedDomainRegistry(
        **body,
        registry_hash=_stable_hash(body),
    )

    verify_oracle_memory_certified_domain_registry(registry)
    return registry


def verify_oracle_memory_certified_domain_registry(
    registry: OracleMemoryCertifiedDomainRegistry,
) -> bool:
    body = asdict(registry)
    supplied = body.pop("registry_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-003 registry hash mismatch")

    if registry.schema_version != SCHEMA_VERSION:
        _reject("OML-003 schema mismatch")

    if registry.engine_id != ENGINE_ID:
        _reject("OML-003 engine mismatch")

    if registry.policy_id != POLICY_ID:
        _reject("OML-003 policy mismatch")

    if registry.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-003 subsystem mismatch")

    if registry.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-003 certified upstream schema mismatch")

    if registry.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-003 certified upstream engine mismatch")

    lineage_hashes = (
        registry.upstream_decision_hash,
        registry.upstream_foundation_report_hash,
        registry.upstream_oit_report_hash,
        registry.upstream_oit_runner_sha256,
        registry.registry_hash,
    )

    if any(len(value) != 64 for value in lineage_hashes):
        _reject("OML-003 lineage hash length invalid")

    if registry.registry_status != REGISTRY_STATUS_CERTIFIED:
        _reject("OML-003 registry status mismatch")

    if registry.domain_count != len(MEMORY_DOMAINS):
        _reject("OML-003 domain count mismatch")

    if tuple(item.domain_id for item in registry.domains) != MEMORY_DOMAINS:
        _reject("OML-003 domain identity or order mismatch")

    for definition in registry.domains:
        verify_oracle_memory_domain_definition(definition)

    required_true = (
        registry.registry_complete,
        registry.domain_order_canonical,
        registry.identities_unique,
        registry.all_domains_inactive,
        registry.all_domains_non_writing,
        registry.all_domains_read_only,
        registry.no_database_access_authorized,
        registry.no_networking_authorized,
        registry.publication_disabled,
        registry.action_authorization_disabled,
        registry.qseries_execution_disabled,
        registry.next_certification_authorized,
    )

    if not all(required_true):
        _reject("OML-003 registry guarantee missing")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_domain_registry import (
    REGISTRY_STATUS_CERTIFIED,
    OracleMemoryDomainRegistryInvariantError,
    build_oracle_memory_certified_domain_registry,
    verify_oracle_memory_certified_domain_registry,
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


def build_oml_002_decision(root: Path):
    fixture = load_module(
        root
        / "test_oit_050_oracle_terminal_final_freeze_and_completion.py",
        "oit_050_fixture_for_oml_003",
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

    return build_oracle_memory_learner_foundation_admission_decision(
        root,
        foundation_report=oml_001,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryDomainRegistryInvariantError:
        return

    raise AssertionError(f"tampered OML-003 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-003 TEST")
    print(" CERTIFIED MEMORY DOMAIN REGISTRY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    admission = build_oml_002_decision(root)

    registry = build_oracle_memory_certified_domain_registry(
        admission_decision=admission,
    )

    assert registry.schema_version == "OML-003"
    assert registry.engine_id == "OML-003"
    assert registry.upstream_schema_version == "OML-002"
    assert registry.upstream_engine_id == "OML-002"
    assert registry.upstream_decision_hash == admission.decision_hash
    assert registry.upstream_foundation_report_hash == (
        admission.upstream_report_hash
    )
    assert registry.upstream_oit_report_hash == (
        admission.upstream_oit_report_hash
    )
    assert registry.upstream_oit_runner_sha256 == (
        admission.upstream_oit_runner_sha256
    )

    assert registry.registry_status == REGISTRY_STATUS_CERTIFIED
    assert registry.domain_count == 8
    assert tuple(item.domain_id for item in registry.domains) == MEMORY_DOMAINS
    assert registry.registry_complete
    assert registry.domain_order_canonical
    assert registry.identities_unique
    assert registry.all_domains_inactive
    assert registry.all_domains_non_writing
    assert registry.all_domains_read_only
    assert registry.no_database_access_authorized
    assert registry.no_networking_authorized
    assert registry.publication_disabled
    assert registry.action_authorization_disabled
    assert registry.qseries_execution_disabled
    assert registry.next_certification_authorized

    for index, definition in enumerate(registry.domains, start=1):
        assert definition.ordinal == index
        assert definition.domain_id == MEMORY_DOMAINS[index - 1]
        assert definition.domain_kind == "memory"
        assert not definition.persistent_storage_authorized
        assert not definition.learning_update_authorized
        assert not definition.runtime_activation_authorized
        assert not definition.database_access_authorized
        assert not definition.networking_authorized
        assert not definition.publication_authorized
        assert not definition.action_authorization_enabled
        assert not definition.qseries_execution_authorized
        assert definition.read_only

    replay = build_oracle_memory_certified_domain_registry(
        admission_decision=admission,
    )

    assert replay == registry
    assert verify_oracle_memory_certified_domain_registry(registry)

    expect_rejection(
        lambda: verify_oracle_memory_certified_domain_registry(
            replace(registry, domain_count=7)
        ),
        "domain count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_domain_registry(
            replace(registry, all_domains_non_writing=False)
        ),
        "non-writing guarantee",
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_domain_registry(
            replace(registry, publication_disabled=False)
        ),
        "publication boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_domain_registry(
            replace(registry, qseries_execution_disabled=False)
        ),
        "Q Series execution boundary",
    )

    print("[PASS] Certified OML-002 admission decision consumed")
    print("[PASS] OML-002 identity and lineage retained")
    print("[PASS] Eight production memory domains registered")
    print("[PASS] Domain identities unique and canonically ordered")
    print("[PASS] Domain definitions deterministic across replay")
    print("[PASS] Every domain remained inactive")
    print("[PASS] Persistent storage remained unauthorized")
    print("[PASS] Learning updates remained unauthorized")
    print("[PASS] Database and networking remained unauthorized")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Every domain remained read-only")
    print("[PASS] Tampered registry states rejected")
    print("[DONE] OML-003 CERTIFIED MEMORY DOMAIN REGISTRY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_actual_oml_002() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_learner_foundation_admission_gate"
    )

    expected = {
        "SCHEMA_VERSION": "OML-002",
        "ENGINE_ID": "OML-002",
        "POLICY_ID": "oracle-memory-learner.foundation-admission-gate.v1",
        "UPSTREAM_SCHEMA_VERSION": "OML-001",
        "UPSTREAM_ENGINE_ID": "OML-001",
    }

    for name, value in expected.items():
        actual = getattr(module, name, None)

        if actual != value:
            raise RuntimeError(
                f"Certified OML-002 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    required = (
        "OracleMemoryLearnerFoundationAdmissionDecision",
        "build_oracle_memory_learner_foundation_admission_decision",
        "verify_oracle_memory_learner_foundation_admission_decision",
        "ADMISSION_STATUS_ADMITTED",
    )

    missing = [name for name in required if not hasattr(module, name)]

    if missing:
        raise RuntimeError(
            "Certified OML-002 missing required symbols: "
            + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-003 FOR-SURE INSTALLER")
    print(" CERTIFIED MEMORY DOMAIN REGISTRY")
    print("=" * 48)
    print("[BOOT] Revision: IMPORT_ALIGNED_FULL_REPLACEMENT")

    try:
        validate_actual_oml_002()
        print("[OK] Actual OML-002 imported and structurally verified")

        upstream = subprocess.run(
            [sys.executable, str(OML_002_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream.returncode:
            raise RuntimeError(
                "OML-002 certification failed with exit code "
                f"{upstream.returncode}"
            )

        production_before = OML_002.read_bytes()
        test_before = OML_002_TEST.read_bytes()

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = "from .oracle_memory_certified_domain_registry import *"
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
                "OML-003 test failed with exit code "
                f"{completed.returncode}"
            )

        if OML_002.read_bytes() != production_before:
            raise RuntimeError("Certified OML-002 production changed")

        if OML_002_TEST.read_bytes() != test_before:
            raise RuntimeError("Certified OML-002 standalone test changed")

        print("[PASS] Certified OML-002 production unchanged")
        print("[PASS] Certified OML-002 standalone test unchanged")
        print("[PASS] OML-003 production registry installed")
        print("[PASS] OML-003 deterministic standalone test installed")
        print("[PASS] Eight memory-domain identities registered")
        print("[PASS] All memory domains remained inactive")
        print("[PASS] Persistent memory remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Database and networking remained unauthorized")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OML-003 CERTIFIED MEMORY DOMAIN REGISTRY INSTALLED")
        return 0

    except (RuntimeError, SyntaxError, ImportError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
