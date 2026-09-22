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
    / "oracle_memory_final_freeze_readiness_"
      "certification_gate_078.py"
)
UPSTREAM_TEST = (
    ROOT
    / "test_oml_078_oracle_memory_final_freeze_"
      "readiness_certification_gate.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_memory_final_freeze_and_completion_"
      "certification_079.py"
)
TEST = (
    ROOT
    / "test_oml_079_oracle_memory_final_freeze_and_"
      "completion_certification.py"
)
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom typing import Any, Mapping\n\nfrom qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (\n    SUBSYSTEM_ID,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_final_freeze_readiness_certification_gate_078 import (\n    NEXT_SUBSYSTEM,\n    OracleMemoryFinalFreezeReadinessReport,\n    verify_oracle_memory_final_freeze_readiness_report,\n)\n\nSCHEMA_VERSION = "OML-079"\nENGINE_ID = "OML-079"\nPOLICY_ID = "oracle-memory.final-freeze-and-completion-certification.v1"\nUPSTREAM_SCHEMA_VERSION = "OML-078"\nUPSTREAM_ENGINE_ID = "OML-078"\nSUBSYSTEM_STATUS = "FROZEN"\nSTATE_READ_ONLY = "oracle_memory_final_frozen_read_only"\nFINAL_FREEZE_MILESTONE = "OML-079"\n\n\nclass OracleMemoryFinalFreezeInvariantError(RuntimeError):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleMemoryFinalFreezeCertificate:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    subsystem_id: str\n    subsystem_status: str\n    final_freeze_milestone: str\n    next_subsystem: str\n    upstream_schema_version: str\n    upstream_engine_id: str\n    upstream_certification_hash: str\n    readiness_manifest_hash: str\n    package_tree_hash: str\n    test_tree_hash: str\n    repository_tree_hash: str\n    source_dependency_certification_hash: str\n    source_dependency_memory_hash: str\n    state: str\n    repository_inventory_frozen: bool\n    deterministic_replay_frozen: bool\n    immutable_lineage_frozen: bool\n    interface_contracts_frozen: bool\n    oracle_terminal_separation_frozen: bool\n    read_only_boundary_frozen: bool\n    persistence_frozen_disabled: bool\n    learning_updates_frozen_disabled: bool\n    runtime_activation_frozen_disabled: bool\n    publication_frozen_disabled: bool\n    action_authorization_frozen_disabled: bool\n    qseries_execution_frozen_disabled: bool\n    further_oml_feature_builds_allowed: bool\n    defect_corrections_only: bool\n    universal_market_discovery_authorized: bool\n    final_freeze_complete: bool\n    read_only: bool\n    certificate_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleMemoryFinalFreezeCompletion:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    subsystem_id: str\n    subsystem_status: str\n    upstream_schema_version: str\n    upstream_engine_id: str\n    upstream_certification_hash: str\n    state: str\n    certificate: OracleMemoryFinalFreezeCertificate\n    final_freeze_complete: bool\n    subsystem_completion_certified: bool\n    downstream_universal_market_discovery_authorized: bool\n    further_oml_feature_builds_allowed: bool\n    defect_corrections_only: bool\n    persistence_enabled: bool\n    learning_updates_enabled: bool\n    runtime_activation_enabled: bool\n    publication_enabled: bool\n    action_authorization_enabled: bool\n    qseries_execution_enabled: bool\n    read_only: bool\n    certification_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(\n                value.items(),\n                key=lambda pair: str(pair[0]),\n            )\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleMemoryFinalFreezeInvariantError(\n        "unsupported OML-079 value type"\n    )\n\n\ndef _stable_hash(value: Any) -> str:\n    return hashlib.sha256(\n        json.dumps(\n            _canonical(value),\n            sort_keys=True,\n            separators=(",", ":"),\n            ensure_ascii=True,\n            allow_nan=False,\n        ).encode("utf-8")\n    ).hexdigest()\n\n\ndef _reject(reason: str) -> None:\n    raise OracleMemoryFinalFreezeInvariantError(reason)\n\n\ndef _require_hash(value: str, label: str) -> None:\n    if not isinstance(value, str) or len(value) != 64:\n        _reject(f"OML-079 invalid {label} length")\n    try:\n        int(value, 16)\n    except ValueError as exc:\n        raise OracleMemoryFinalFreezeInvariantError(\n            f"OML-079 invalid {label} hexadecimal value"\n        ) from exc\n\n\ndef build_oracle_memory_final_freeze_completion(\n    *,\n    readiness: OracleMemoryFinalFreezeReadinessReport,\n) -> OracleMemoryFinalFreezeCompletion:\n    verify_oracle_memory_final_freeze_readiness_report(readiness)\n\n    if readiness.schema_version != UPSTREAM_SCHEMA_VERSION:\n        _reject("OML-079 upstream schema mismatch")\n    if readiness.engine_id != UPSTREAM_ENGINE_ID:\n        _reject("OML-079 upstream engine mismatch")\n    if not readiness.final_freeze_ready:\n        _reject("OML-079 readiness gate not ready")\n    if not readiness.downstream_final_freeze_authorized:\n        _reject("OML-079 final freeze not authorized")\n    if readiness.further_feature_builds_allowed:\n        _reject("OML-079 upstream permits further feature builds")\n    if not readiness.correction_builds_allowed_only_for_defects:\n        _reject("OML-079 defect-only correction policy missing")\n    if not readiness.read_only:\n        _reject("OML-079 readiness report not read-only")\n    if readiness.manifest.next_subsystem != NEXT_SUBSYSTEM:\n        _reject("OML-079 next subsystem mismatch")\n    if readiness.manifest.final_freeze_milestone != FINAL_FREEZE_MILESTONE:\n        _reject("OML-079 final freeze milestone mismatch")\n\n    certificate_body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "subsystem_id": SUBSYSTEM_ID,\n        "subsystem_status": SUBSYSTEM_STATUS,\n        "final_freeze_milestone": FINAL_FREEZE_MILESTONE,\n        "next_subsystem": NEXT_SUBSYSTEM,\n        "upstream_schema_version": readiness.schema_version,\n        "upstream_engine_id": readiness.engine_id,\n        "upstream_certification_hash": readiness.certification_hash,\n        "readiness_manifest_hash": readiness.manifest.manifest_hash,\n        "package_tree_hash": readiness.manifest.package_tree_hash,\n        "test_tree_hash": readiness.manifest.test_tree_hash,\n        "repository_tree_hash": readiness.manifest.repository_tree_hash,\n        "source_dependency_certification_hash": (\n            readiness.manifest.source_dependency_certification_hash\n        ),\n        "source_dependency_memory_hash": (\n            readiness.manifest.source_dependency_memory_hash\n        ),\n        "state": STATE_READ_ONLY,\n        "repository_inventory_frozen": True,\n        "deterministic_replay_frozen": True,\n        "immutable_lineage_frozen": True,\n        "interface_contracts_frozen": True,\n        "oracle_terminal_separation_frozen": True,\n        "read_only_boundary_frozen": True,\n        "persistence_frozen_disabled": True,\n        "learning_updates_frozen_disabled": True,\n        "runtime_activation_frozen_disabled": True,\n        "publication_frozen_disabled": True,\n        "action_authorization_frozen_disabled": True,\n        "qseries_execution_frozen_disabled": True,\n        "further_oml_feature_builds_allowed": False,\n        "defect_corrections_only": True,\n        "universal_market_discovery_authorized": True,\n        "final_freeze_complete": True,\n        "read_only": True,\n    }\n    certificate = OracleMemoryFinalFreezeCertificate(\n        **certificate_body,\n        certificate_hash=_stable_hash(certificate_body),\n    )\n    verify_oracle_memory_final_freeze_certificate(certificate)\n\n    completion_body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "subsystem_id": SUBSYSTEM_ID,\n        "subsystem_status": SUBSYSTEM_STATUS,\n        "upstream_schema_version": readiness.schema_version,\n        "upstream_engine_id": readiness.engine_id,\n        "upstream_certification_hash": readiness.certification_hash,\n        "state": STATE_READ_ONLY,\n        "certificate": certificate,\n        "final_freeze_complete": True,\n        "subsystem_completion_certified": True,\n        "downstream_universal_market_discovery_authorized": True,\n        "further_oml_feature_builds_allowed": False,\n        "defect_corrections_only": True,\n        "persistence_enabled": False,\n        "learning_updates_enabled": False,\n        "runtime_activation_enabled": False,\n        "publication_enabled": False,\n        "action_authorization_enabled": False,\n        "qseries_execution_enabled": False,\n        "read_only": True,\n    }\n    completion = OracleMemoryFinalFreezeCompletion(\n        **completion_body,\n        certification_hash=_stable_hash(completion_body),\n    )\n    verify_oracle_memory_final_freeze_completion(completion)\n    return completion\n\n\ndef verify_oracle_memory_final_freeze_certificate(\n    certificate: OracleMemoryFinalFreezeCertificate,\n) -> bool:\n    body = asdict(certificate)\n    supplied = body.pop("certificate_hash")\n    if _stable_hash(body) != supplied:\n        _reject("OML-079 certificate hash mismatch")\n\n    if certificate.schema_version != SCHEMA_VERSION:\n        _reject("OML-079 certificate schema mismatch")\n    if certificate.engine_id != ENGINE_ID:\n        _reject("OML-079 certificate engine mismatch")\n    if certificate.policy_id != POLICY_ID:\n        _reject("OML-079 certificate policy mismatch")\n    if certificate.subsystem_id != SUBSYSTEM_ID:\n        _reject("OML-079 certificate subsystem mismatch")\n    if certificate.subsystem_status != SUBSYSTEM_STATUS:\n        _reject("OML-079 subsystem not frozen")\n    if certificate.final_freeze_milestone != FINAL_FREEZE_MILESTONE:\n        _reject("OML-079 milestone mismatch")\n    if certificate.next_subsystem != NEXT_SUBSYSTEM:\n        _reject("OML-079 next subsystem mismatch")\n    if certificate.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:\n        _reject("OML-079 certificate upstream schema mismatch")\n    if certificate.upstream_engine_id != UPSTREAM_ENGINE_ID:\n        _reject("OML-079 certificate upstream engine mismatch")\n    if certificate.state != STATE_READ_ONLY:\n        _reject("OML-079 certificate state mismatch")\n\n    for value in (\n        certificate.upstream_certification_hash,\n        certificate.readiness_manifest_hash,\n        certificate.package_tree_hash,\n        certificate.test_tree_hash,\n        certificate.repository_tree_hash,\n        certificate.source_dependency_certification_hash,\n        certificate.source_dependency_memory_hash,\n        certificate.certificate_hash,\n    ):\n        _require_hash(value, "certificate hash")\n\n    required = (\n        certificate.repository_inventory_frozen,\n        certificate.deterministic_replay_frozen,\n        certificate.immutable_lineage_frozen,\n        certificate.interface_contracts_frozen,\n        certificate.oracle_terminal_separation_frozen,\n        certificate.read_only_boundary_frozen,\n        certificate.persistence_frozen_disabled,\n        certificate.learning_updates_frozen_disabled,\n        certificate.runtime_activation_frozen_disabled,\n        certificate.publication_frozen_disabled,\n        certificate.action_authorization_frozen_disabled,\n        certificate.qseries_execution_frozen_disabled,\n        certificate.defect_corrections_only,\n        certificate.universal_market_discovery_authorized,\n        certificate.final_freeze_complete,\n        certificate.read_only,\n    )\n    if not all(required):\n        _reject("OML-079 certificate guarantee missing")\n    if certificate.further_oml_feature_builds_allowed:\n        _reject("OML-079 certificate permits further OML feature builds")\n    return True\n\n\ndef verify_oracle_memory_final_freeze_completion(\n    completion: OracleMemoryFinalFreezeCompletion,\n) -> bool:\n    body = asdict(completion)\n    supplied = body.pop("certification_hash")\n    if _stable_hash(body) != supplied:\n        _reject("OML-079 completion hash mismatch")\n\n    if completion.schema_version != SCHEMA_VERSION:\n        _reject("OML-079 schema mismatch")\n    if completion.engine_id != ENGINE_ID:\n        _reject("OML-079 engine mismatch")\n    if completion.policy_id != POLICY_ID:\n        _reject("OML-079 policy mismatch")\n    if completion.subsystem_id != SUBSYSTEM_ID:\n        _reject("OML-079 subsystem mismatch")\n    if completion.subsystem_status != SUBSYSTEM_STATUS:\n        _reject("OML-079 completion status mismatch")\n    if completion.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:\n        _reject("OML-079 upstream schema mismatch")\n    if completion.upstream_engine_id != UPSTREAM_ENGINE_ID:\n        _reject("OML-079 upstream engine mismatch")\n    if completion.state != STATE_READ_ONLY:\n        _reject("OML-079 state mismatch")\n\n    _require_hash(\n        completion.upstream_certification_hash,\n        "upstream certification hash",\n    )\n    _require_hash(completion.certification_hash, "completion hash")\n    verify_oracle_memory_final_freeze_certificate(completion.certificate)\n\n    if completion.upstream_certification_hash != (\n        completion.certificate.upstream_certification_hash\n    ):\n        _reject("OML-079 upstream lineage mismatch")\n\n    required = (\n        completion.final_freeze_complete,\n        completion.subsystem_completion_certified,\n        completion.downstream_universal_market_discovery_authorized,\n        completion.defect_corrections_only,\n        completion.read_only,\n    )\n    if not all(required):\n        _reject("OML-079 completion guarantee missing")\n    if completion.further_oml_feature_builds_allowed:\n        _reject("OML-079 permits further OML feature builds")\n\n    forbidden = (\n        completion.persistence_enabled,\n        completion.learning_updates_enabled,\n        completion.runtime_activation_enabled,\n        completion.publication_enabled,\n        completion.action_authorization_enabled,\n        completion.qseries_execution_enabled,\n    )\n    if any(forbidden):\n        _reject("OML-079 forbidden capability enabled")\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport importlib.util\nimport sys\nfrom dataclasses import replace\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_memory.oracle_memory_final_freeze_and_completion_certification_079 import (\n    OracleMemoryFinalFreezeInvariantError,\n    build_oracle_memory_final_freeze_completion,\n    verify_oracle_memory_final_freeze_completion,\n)\n\n\ndef load_module(path: Path, name: str):\n    specification = importlib.util.spec_from_file_location(name, path)\n    if specification is None or specification.loader is None:\n        raise RuntimeError(f"unable to load fixture: {path}")\n    module = importlib.util.module_from_spec(specification)\n    sys.modules[name] = module\n    specification.loader.exec_module(module)\n    return module\n\n\ndef expect_rejection(callable_object, label: str) -> None:\n    try:\n        callable_object()\n    except OracleMemoryFinalFreezeInvariantError:\n        return\n    raise AssertionError(f"tampered OML-079 {label} accepted")\n\n\ndef build_final_freeze(root: Path):\n    fixture_078 = load_module(\n        root\n        / "test_oml_078_oracle_memory_final_freeze_"\n        "readiness_certification_gate.py",\n        "oml_078_fixture_for_oml_079",\n    )\n    readiness, dependencies = fixture_078.build_freeze_readiness(root)\n    completion = build_oracle_memory_final_freeze_completion(\n        readiness=readiness,\n    )\n    return completion, readiness\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OML-079 TEST")\n    print(" FINAL FREEZE AND COMPLETION CERTIFICATION")\n    print("=" * 48)\n\n    root = Path(__file__).resolve().parent\n    completion, readiness = build_final_freeze(root)\n\n    assert completion.schema_version == "OML-079"\n    assert completion.engine_id == "OML-079"\n    assert completion.subsystem_status == "FROZEN"\n    assert completion.upstream_schema_version == "OML-078"\n    assert completion.upstream_engine_id == "OML-078"\n    assert completion.upstream_certification_hash == (\n        readiness.certification_hash\n    )\n    assert completion.final_freeze_complete\n    assert completion.subsystem_completion_certified\n    assert completion.downstream_universal_market_discovery_authorized\n    assert not completion.further_oml_feature_builds_allowed\n    assert completion.defect_corrections_only\n    assert completion.read_only\n\n    certificate = completion.certificate\n    assert certificate.final_freeze_milestone == "OML-079"\n    assert certificate.next_subsystem == "universal_market_discovery"\n    assert certificate.readiness_manifest_hash == (\n        readiness.manifest.manifest_hash\n    )\n    assert certificate.package_tree_hash == (\n        readiness.manifest.package_tree_hash\n    )\n    assert certificate.test_tree_hash == readiness.manifest.test_tree_hash\n    assert certificate.repository_tree_hash == (\n        readiness.manifest.repository_tree_hash\n    )\n    assert certificate.interface_contracts_frozen\n    assert certificate.universal_market_discovery_authorized\n    assert certificate.final_freeze_complete\n    assert not certificate.further_oml_feature_builds_allowed\n\n    replay, _ = build_final_freeze(root)\n    assert replay == completion\n    assert verify_oracle_memory_final_freeze_completion(completion)\n\n    expect_rejection(\n        lambda: verify_oracle_memory_final_freeze_completion(\n            replace(completion, further_oml_feature_builds_allowed=True)\n        ),\n        "feature authorization",\n    )\n    expect_rejection(\n        lambda: verify_oracle_memory_final_freeze_completion(\n            replace(completion, qseries_execution_enabled=True)\n        ),\n        "Q Series execution",\n    )\n\n    assert not completion.persistence_enabled\n    assert not completion.learning_updates_enabled\n    assert not completion.runtime_activation_enabled\n    assert not completion.publication_enabled\n    assert not completion.action_authorization_enabled\n    assert not completion.qseries_execution_enabled\n\n    print("[PASS] Certified OML-078 readiness consumed read-only")\n    print("[PASS] Readiness manifest and repository hashes sealed")\n    print("[PASS] Oracle Memory interfaces frozen")\n    print("[PASS] Deterministic replay and immutable lineage frozen")\n    print("[PASS] Oracle Terminal separation frozen")\n    print("[PASS] Active capabilities permanently frozen disabled")\n    print("[PASS] Further OML feature builds prohibited")\n    print("[PASS] Defect corrections remain the only allowed OML changes")\n    print("[PASS] Universal Market Discovery authorized next")\n    print("[PASS] Tampered final-freeze completions rejected")\n    print("[DONE] OML-079 ORACLE MEMORY FINAL FREEZE PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_current_repository() -> None:
    required = (UPSTREAM, UPSTREAM_TEST)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified files missing: " + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_final_freeze_readiness_"
        "certification_gate_078"
    )
    if getattr(module, "SCHEMA_VERSION", None) != "OML-078":
        raise RuntimeError("OML-078 SCHEMA_VERSION mismatch")
    if getattr(module, "ENGINE_ID", None) != "OML-078":
        raise RuntimeError("OML-078 ENGINE_ID mismatch")
    if getattr(module, "FINAL_FREEZE_MILESTONE", None) != "OML-079":
        raise RuntimeError("OML-078 final-freeze milestone mismatch")
    if getattr(module, "NEXT_SUBSYSTEM", None) != (
        "universal_market_discovery"
    ):
        raise RuntimeError("OML-078 next subsystem mismatch")

    fields = set(
        module.OracleMemoryFinalFreezeReadinessReport.__dataclass_fields__
    )
    required_fields = {
        "manifest",
        "final_freeze_ready",
        "downstream_final_freeze_authorized",
        "further_feature_builds_allowed",
        "correction_builds_allowed_only_for_defects",
        "read_only",
        "certification_hash",
    }
    missing_fields = sorted(required_fields - fields)
    if missing_fields:
        raise RuntimeError(
            "OML-078 dataclass fields missing: "
            + ", ".join(missing_fields)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-079 INSTALLER")
    print(" ORACLE MEMORY FINAL FREEZE AND COMPLETION")
    print("=" * 48)
    print(
        "[BOOT] Revision: "
        "CURRENT_REPOSITORY_OML_078_FINAL_FREEZE_ALIGNMENT"
    )

    try:
        validate_current_repository()
        print("[OK] Current OML-078 constants inspected")
        print("[OK] Current OML-078 readiness dataclass inspected")

        tracked = {
            path: path.read_bytes()
            for path in (UPSTREAM, UPSTREAM_TEST)
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_final_freeze_and_completion_"
            "certification_079 import *"
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

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OML-079 test failed with exit code {completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Complete OML-079 production replacement installed")
        print("[PASS] Complete deterministic standalone test installed")
        print("[PASS] Certified OML-078 files unchanged")
        print("[PASS] Oracle Memory final freeze certified")
        print("[PASS] Oracle Memory subsystem completion certified")
        print("[PASS] Deterministic replay and immutable lineage frozen")
        print("[PASS] Oracle Terminal separation frozen")
        print("[PASS] Persistence frozen disabled")
        print("[PASS] Learning updates frozen disabled")
        print("[PASS] Runtime activation frozen disabled")
        print("[PASS] Publication frozen disabled")
        print("[PASS] Action authorization frozen disabled")
        print("[PASS] Q Series execution frozen disabled")
        print("[PASS] Universal Market Discovery authorized next")
        print("[DONE] OML-079 ORACLE MEMORY FROZEN AND COMPLETE")
        return 0

    except (
        RuntimeError,
        SyntaxError,
        ImportError,
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
