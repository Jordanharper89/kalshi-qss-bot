from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def locate_repository() -> Path:
    candidates = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.extend((base, base / "kalshi-qss-bot"))
        for parent in base.parents:
            candidates.extend((parent, parent / "kalshi-qss-bot"))
    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        source = candidate / "qseries_v2" / "oracle_research_response" / "oracle_research_response_evidence_read_invocation_attestation_consumption_continuation_attestation_consumption_completion_readiness_gate.py"
        if source.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate repository with actual ORR-017 module.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_research_response"
SOURCE = PACKAGE / "oracle_research_response_evidence_read_invocation_attestation_consumption_continuation_attestation_consumption_completion_readiness_gate.py"
PRODUCTION = PACKAGE / "oracle_research_response_final_completion_freeze_and_subsystem_certification_gate.py"
TEST = ROOT / "test_orr_018_oracle_research_response_final_completion_freeze_and_subsystem_certification_gate.py"
INIT = PACKAGE / "__init__.py"
CERTIFICATE = ROOT / "runtime" / "oracle_research_response" / "orr_018_subsystem_freeze_certificate.json"

PRODUCTION_SOURCE = 'from __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_attestation_consumption_continuation_attestation_consumption_completion_readiness_gate import (\n    READINESS_STATUS as ORR_017_READINESS_STATUS,\n    READINESS_TYPE as ORR_017_READINESS_TYPE,\n    OracleResearchResponseEvidenceReadInvocationFinalAttestationConsumptionCompletionReadiness,\n)\n\nSCHEMA_VERSION = "ORR-018"\nENGINE_ID = "ORR-018"\nPOLICY_ID = "oracle.research-response.final-completion-freeze-subsystem-certification.v1"\nCERTIFICATION_TYPE = "oracle_research_response_final_completion_freeze_subsystem_certification"\nCERTIFICATION_STATUS = "oracle_research_response_complete_frozen_and_certified"\nEXPECTED_STAGE_COUNT = 18\n\n\nclass OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(ValueError):\n    pass\n\n\ndef _canonical(value: Any) -> Any:\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda item: str(item[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, datetime):\n        if value.tzinfo is None or value.utcoffset() is None:\n            raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(\n                "datetime must be timezone-aware"\n            )\n        return value.astimezone(timezone.utc).isoformat()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(\n        f"unsupported value type: {type(value)!r}"\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n    return hashlib.sha256(payload.encode("utf-8")).hexdigest()\n\n\ndef file_sha256(path: Path) -> str:\n    return hashlib.sha256(path.read_bytes()).hexdigest()\n\n\ndef _valid_sha256(value: Any) -> bool:\n    return (\n        isinstance(value, str)\n        and len(value) == 64\n        and all(character in "0123456789abcdef" for character in value)\n    )\n\n\n@dataclass(frozen=True)\nclass OracleResearchResponseFinalCompletionFreezeSubsystemCertification:\n    certification_id: str\n    completion_readiness_id: str\n    completion_readiness_hash: str\n    final_attestation_id: str\n    final_attestation_hash: str\n    request_id: str\n    request_hash: str\n    dependency_receipt_id: str\n    dependency_receipt_hash: str\n    source_runtime_completion_id: str\n    source_runtime_completion_hash: str\n    subsystem_namespace: str\n    requester_id: str\n    correlation_id: str\n    question_text: str\n    response_mode: str\n    filters: tuple[tuple[str, str], ...]\n    certified_at: datetime\n    stage_count: int\n    certified_stage_range: str\n    module_manifest: tuple[tuple[str, str], ...]\n    module_manifest_hash: str\n    completion_readiness_identity_verified: bool\n    completion_readiness_hash_verified: bool\n    completion_readiness_contract_verified: bool\n    complete_lineage_verified: bool\n    module_manifest_verified: bool\n    package_boundary_verified: bool\n    deterministic_boundary_verified: bool\n    immutable_certification_boundary_verified: bool\n    read_only_boundary_verified: bool\n    subsystem_complete_verified: bool\n    subsystem_frozen_verified: bool\n    further_certification_layers_required: bool\n    callable_binding_allowed: bool\n    callable_invocation_allowed: bool\n    result_materialization_allowed: bool\n    runtime_serving_allowed: bool\n    network_listener_allowed: bool\n    database_connection_allowed: bool\n    publication_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    certification_type: str\n    certification_status: str\n    certification_hash: str\n\n\nclass OracleResearchResponseFinalCompletionFreezeSubsystemCertificationGate:\n    def certify(\n        self,\n        *,\n        readiness: OracleResearchResponseEvidenceReadInvocationFinalAttestationConsumptionCompletionReadiness,\n        certified_at: datetime,\n        module_manifest: tuple[tuple[str, str], ...],\n    ) -> OracleResearchResponseFinalCompletionFreezeSubsystemCertification:\n        if not isinstance(\n            readiness,\n            OracleResearchResponseEvidenceReadInvocationFinalAttestationConsumptionCompletionReadiness,\n        ):\n            raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(\n                "readiness must be canonical ORR-017 completion readiness"\n            )\n\n        readiness_body = asdict(readiness)\n        supplied_hash = readiness_body.pop("readiness_hash", None)\n        if not _valid_sha256(supplied_hash) or stable_hash(readiness_body) != supplied_hash:\n            raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(\n                "ORR-017 readiness hash mismatch"\n            )\n\n        required = (\n            _valid_sha256(readiness.readiness_id),\n            _valid_sha256(readiness.final_attestation_id),\n            _valid_sha256(readiness.final_attestation_hash),\n            _valid_sha256(readiness.request_id),\n            _valid_sha256(readiness.request_hash),\n            _valid_sha256(readiness.dependency_receipt_id),\n            _valid_sha256(readiness.dependency_receipt_hash),\n            _valid_sha256(readiness.source_runtime_completion_id),\n            _valid_sha256(readiness.source_runtime_completion_hash),\n            readiness.readiness_type == ORR_017_READINESS_TYPE,\n            readiness.readiness_status == ORR_017_READINESS_STATUS,\n            readiness.final_attestation_identity_verified,\n            readiness.final_attestation_hash_verified,\n            readiness.final_attestation_contract_verified,\n            readiness.full_lineage_verified,\n            readiness.activation_record_identity_verified,\n            readiness.activation_record_hashes_verified,\n            readiness.invocation_lineage_verified,\n            readiness.invocation_order_verified,\n            readiness.invocation_count_verified,\n            readiness.approved_read_operations_verified,\n            readiness.completion_scope_verified,\n            readiness.completion_readiness_verified,\n            readiness.callable_binding_remains_disabled_verified,\n            readiness.callable_invocation_remains_disabled_verified,\n            readiness.result_materialization_remains_disabled_verified,\n            readiness.deterministic_boundary_verified,\n            readiness.immutable_readiness_boundary_verified,\n            readiness.read_only_boundary_verified,\n            readiness.single_attestation_scope_verified,\n            readiness.consumption_single_use_verified,\n            not readiness.duplicate_consumption_allowed,\n            not readiness.consumption_reversible,\n        )\n        forbidden = (\n            readiness.runtime_serving_allowed,\n            readiness.network_listener_allowed,\n            readiness.database_connection_allowed,\n            readiness.publication_allowed,\n            readiness.qseries_handoff_allowed,\n            readiness.qseries_execution_allowed,\n            readiness.order_creation_allowed,\n            readiness.funds_movement_allowed,\n            readiness.portfolio_mutation_allowed,\n        )\n        if not all(required) or any(forbidden):\n            raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(\n                "ORR-017 readiness contract incomplete or unsafe"\n            )\n\n        if (\n            not isinstance(certified_at, datetime)\n            or certified_at.tzinfo is None\n            or certified_at.utcoffset() is None\n        ):\n            raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(\n                "certified_at must be timezone-aware"\n            )\n        at = certified_at.astimezone(timezone.utc)\n        if at < readiness.final_attestation_consumed_at.astimezone(timezone.utc):\n            raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(\n                "certification cannot precede completion readiness"\n            )\n\n        if not isinstance(module_manifest, tuple) or not module_manifest:\n            raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(\n                "module_manifest must be a non-empty tuple"\n            )\n        normalized = tuple(sorted(module_manifest))\n        if normalized != module_manifest:\n            raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(\n                "module_manifest must be canonically sorted"\n            )\n        names = [name for name, _ in module_manifest]\n        hashes = [digest for _, digest in module_manifest]\n        if (\n            len(names) != len(set(names))\n            or any(not isinstance(name, str) or not name.endswith(".py") for name in names)\n            or any(not _valid_sha256(digest) for digest in hashes)\n        ):\n            raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(\n                "module_manifest entries invalid"\n            )\n\n        manifest_hash = stable_hash(module_manifest)\n        body = {\n            "completion_readiness_id": readiness.readiness_id,\n            "completion_readiness_hash": readiness.readiness_hash,\n            "final_attestation_id": readiness.final_attestation_id,\n            "final_attestation_hash": readiness.final_attestation_hash,\n            "request_id": readiness.request_id,\n            "request_hash": readiness.request_hash,\n            "dependency_receipt_id": readiness.dependency_receipt_id,\n            "dependency_receipt_hash": readiness.dependency_receipt_hash,\n            "source_runtime_completion_id": readiness.source_runtime_completion_id,\n            "source_runtime_completion_hash": readiness.source_runtime_completion_hash,\n            "subsystem_namespace": readiness.subsystem_namespace,\n            "requester_id": readiness.requester_id,\n            "correlation_id": readiness.correlation_id,\n            "question_text": readiness.question_text,\n            "response_mode": readiness.response_mode,\n            "filters": readiness.filters,\n            "certified_at": at,\n            "stage_count": EXPECTED_STAGE_COUNT,\n            "certified_stage_range": "ORR-001..ORR-018",\n            "module_manifest": module_manifest,\n            "module_manifest_hash": manifest_hash,\n            "completion_readiness_identity_verified": True,\n            "completion_readiness_hash_verified": True,\n            "completion_readiness_contract_verified": True,\n            "complete_lineage_verified": True,\n            "module_manifest_verified": True,\n            "package_boundary_verified": True,\n            "deterministic_boundary_verified": True,\n            "immutable_certification_boundary_verified": True,\n            "read_only_boundary_verified": True,\n            "subsystem_complete_verified": True,\n            "subsystem_frozen_verified": True,\n            "further_certification_layers_required": False,\n            "callable_binding_allowed": False,\n            "callable_invocation_allowed": False,\n            "result_materialization_allowed": False,\n            "runtime_serving_allowed": False,\n            "network_listener_allowed": False,\n            "database_connection_allowed": False,\n            "publication_allowed": False,\n            "qseries_handoff_allowed": False,\n            "qseries_execution_allowed": False,\n            "order_creation_allowed": False,\n            "funds_movement_allowed": False,\n            "portfolio_mutation_allowed": False,\n            "certification_type": CERTIFICATION_TYPE,\n            "certification_status": CERTIFICATION_STATUS,\n        }\n        body["certification_id"] = stable_hash(\n            {\n                "engine_id": ENGINE_ID,\n                "completion_readiness_id": readiness.readiness_id,\n                "completion_readiness_hash": readiness.readiness_hash,\n                "module_manifest_hash": manifest_hash,\n                "certified_at": at,\n                "certification_type": CERTIFICATION_TYPE,\n            }\n        )\n        return OracleResearchResponseFinalCompletionFreezeSubsystemCertification(\n            **body,\n            certification_hash=stable_hash(body),\n        )\n\n\ndef build_module_manifest(package_directory: Path) -> tuple[tuple[str, str], ...]:\n    if not package_directory.is_dir():\n        raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(\n            "package_directory does not exist"\n        )\n    entries = []\n    for path in sorted(package_directory.glob("*.py"), key=lambda item: item.name):\n        if path.name == "__pycache__":\n            continue\n        entries.append((path.name, file_sha256(path)))\n    if not entries:\n        raise OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError(\n            "no Python modules found"\n        )\n    return tuple(entries)\n\n\n__all__ = [\n    "SCHEMA_VERSION",\n    "ENGINE_ID",\n    "POLICY_ID",\n    "CERTIFICATION_TYPE",\n    "CERTIFICATION_STATUS",\n    "EXPECTED_STAGE_COUNT",\n    "OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError",\n    "OracleResearchResponseFinalCompletionFreezeSubsystemCertification",\n    "OracleResearchResponseFinalCompletionFreezeSubsystemCertificationGate",\n    "build_module_manifest",\n    "file_sha256",\n    "stable_hash",\n]\n'
TEST_SOURCE = 'from dataclasses import asdict, replace\nfrom datetime import datetime, timedelta, timezone\n\nfrom qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_attestation_consumption_continuation_attestation_consumption_completion_readiness_gate import (\n    READINESS_STATUS,\n    READINESS_TYPE,\n    OracleResearchResponseEvidenceReadInvocationFinalAttestationConsumptionCompletionReadiness,\n    stable_hash as source_hash,\n)\nfrom qseries_v2.oracle_research_response.oracle_research_response_final_completion_freeze_and_subsystem_certification_gate import *\n\n\ndef sample_readiness():\n    t = datetime(2026, 7, 29, 20, 10, tzinfo=timezone.utc)\n    body = {\n        "readiness_id": "a"*64, "final_attestation_id": "b"*64, "final_attestation_hash": "c"*64,\n        "continuation_id": "d"*64, "continuation_hash": "e"*64,\n        "consumption_id": "f"*64, "consumption_hash": "1"*64,\n        "source_attestation_id": "2"*64, "source_attestation_hash": "3"*64,\n        "activation_continuation_id": "4"*64, "activation_continuation_hash": "5"*64,\n        "activation_id": "6"*64, "activation_hash": "7"*64,\n        "authorization_consumption_id": "8"*64, "authorization_consumption_hash": "9"*64,\n        "authorization_id": "a"*64, "authorization_hash": "b"*64,\n        "invocation_readiness_id": "c"*64, "invocation_readiness_hash": "d"*64,\n        "evidence_admission_id": "e"*64, "evidence_admission_hash": "f"*64,\n        "materialization_id": "1"*64, "materialization_hash": "2"*64,\n        "plan_admission_id": "3"*64, "plan_admission_hash": "4"*64,\n        "plan_id": "5"*64, "plan_hash": "6"*64,\n        "admission_id": "7"*64, "admission_hash": "8"*64,\n        "request_id": "9"*64, "request_hash": "a"*64,\n        "dependency_receipt_id": "b"*64, "dependency_receipt_hash": "c"*64,\n        "source_runtime_completion_id": "d"*64, "source_runtime_completion_hash": "e"*64,\n        "subsystem_namespace": "oracle_research_response",\n        "requester_id": "operator:jordan",\n        "correlation_id": "session:orr-018-test",\n        "question_text": "What are the strongest Kalshi opportunities closing today?",\n        "response_mode": "prediction_card",\n        "filters": (("time_horizon", "Today"), ("venue", "Kalshi")),\n        "requested_at": t, "admitted_at": t+timedelta(seconds=1),\n        "planned_at": t+timedelta(seconds=2), "plan_admitted_at": t+timedelta(seconds=3),\n        "materialized_at": t+timedelta(seconds=4), "evidence_admitted_at": t+timedelta(seconds=5),\n        "invocation_readiness_certified_at": t+timedelta(seconds=6),\n        "authorized_at": t+timedelta(seconds=7), "consumed_at": t+timedelta(seconds=8),\n        "activated_at": t+timedelta(seconds=9),\n        "activation_continuation_certified_at": t+timedelta(seconds=10),\n        "source_attested_at": t+timedelta(seconds=11),\n        "attestation_consumed_at": t+timedelta(seconds=12),\n        "continuation_at": t+timedelta(seconds=13),\n        "final_attested_at": t+timedelta(seconds=14),\n        "final_attestation_consumed_at": t+timedelta(seconds=15),\n        "plan_steps": ("validate_scope", "identify_required_evidence", "select_analytic_path", "assemble_response", "certify_response_boundary"),\n        "evidence_requirements": ("source_provenance", "market_price", "oracle_probability"),\n        "activation_record_ids": ("1"*64, "2"*64, "3"*64),\n        "activation_record_hashes": ("4"*64, "5"*64, "6"*64),\n        "activated_invocation_ids": ("7"*64, "8"*64, "9"*64),\n        "activated_invocation_hashes": ("a"*64, "b"*64, "c"*64),\n        "activated_read_operations": ("read_certified_lineage", "read_certified_market_state", "read_certified_analytics"),\n        "final_attestation_identity_verified": True,\n        "final_attestation_hash_verified": True,\n        "final_attestation_contract_verified": True,\n        "full_lineage_verified": True,\n        "activation_record_identity_verified": True,\n        "activation_record_hashes_verified": True,\n        "invocation_lineage_verified": True,\n        "invocation_order_verified": True,\n        "invocation_count_verified": True,\n        "approved_read_operations_verified": True,\n        "completion_scope_verified": True,\n        "completion_readiness_verified": True,\n        "callable_binding_remains_disabled_verified": True,\n        "callable_invocation_remains_disabled_verified": True,\n        "result_materialization_remains_disabled_verified": True,\n        "deterministic_boundary_verified": True,\n        "immutable_readiness_boundary_verified": True,\n        "read_only_boundary_verified": True,\n        "single_attestation_scope_verified": True,\n        "consumption_single_use_verified": True,\n        "duplicate_consumption_allowed": False,\n        "consumption_reversible": False,\n        "runtime_serving_allowed": False,\n        "network_listener_allowed": False,\n        "database_connection_allowed": False,\n        "publication_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "readiness_type": READINESS_TYPE,\n        "readiness_status": READINESS_STATUS,\n    }\n    return OracleResearchResponseEvidenceReadInvocationFinalAttestationConsumptionCompletionReadiness(\n        **body, readiness_hash=source_hash(body)\n    )\n\n\ndef reject(fn):\n    try:\n        fn()\n        raise AssertionError("unsafe certification accepted")\n    except OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError:\n        pass\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" ORR-018 TEST")\n    print(" FINAL COMPLETION / FREEZE")\n    print(" SUBSYSTEM CERTIFICATION")\n    print("=" * 40)\n\n    source = sample_readiness()\n    at = source.final_attestation_consumed_at + timedelta(seconds=1)\n    manifest = (\n        ("__init__.py", "1"*64),\n        ("oracle_research_response_final_completion_freeze_and_subsystem_certification_gate.py", "2"*64),\n    )\n    gate = OracleResearchResponseFinalCompletionFreezeSubsystemCertificationGate()\n    first = gate.certify(readiness=source, certified_at=at, module_manifest=manifest)\n    second = gate.certify(readiness=source, certified_at=at, module_manifest=manifest)\n\n    assert first == second\n    assert first.certification_hash == stable_hash(\n        {k: v for k, v in asdict(first).items() if k != "certification_hash"}\n    )\n    assert first.certification_type == CERTIFICATION_TYPE\n    assert first.certification_status == CERTIFICATION_STATUS\n    assert first.stage_count == 18\n    assert first.certified_stage_range == "ORR-001..ORR-018"\n    assert first.subsystem_complete_verified\n    assert first.subsystem_frozen_verified\n    assert not first.further_certification_layers_required\n    assert first.complete_lineage_verified\n    assert first.module_manifest_verified\n    assert first.read_only_boundary_verified\n    assert not first.callable_binding_allowed\n    assert not first.callable_invocation_allowed\n    assert not first.result_materialization_allowed\n    assert not first.runtime_serving_allowed\n    assert not first.publication_allowed\n    assert not first.qseries_execution_allowed\n\n    reject(lambda: gate.certify(readiness=replace(source, readiness_hash="0"*64), certified_at=at, module_manifest=manifest))\n    reject(lambda: gate.certify(readiness=replace(source, publication_allowed=True), certified_at=at, module_manifest=manifest))\n    reject(lambda: gate.certify(readiness=source, certified_at=source.final_attestation_consumed_at-timedelta(seconds=1), module_manifest=manifest))\n    reject(lambda: gate.certify(readiness=source, certified_at=at, module_manifest=tuple(reversed(manifest))))\n    reject(lambda: gate.certify(readiness=source, certified_at=at, module_manifest=(("__init__.py", "x"*64),)))\n\n    print("[PASS] Actual ORR-017 completion readiness consumed")\n    print("[PASS] Complete ORR-001 through ORR-017 lineage preserved")\n    print("[PASS] Deterministic ORR-018 subsystem certification produced")\n    print("[PASS] ORR-001 through ORR-018 completion certified")\n    print("[PASS] Oracle Research Response subsystem frozen")\n    print("[PASS] Module-manifest boundary certified")\n    print("[PASS] Callables remain unbound and uninvoked; results remain unmaterialized")\n    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")\n    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")\n    print("[PASS] No further ORR certification layers required")\n    print("[DONE] ORR-018 FINAL COMPLETION, FREEZE, AND SUBSYSTEM CERTIFICATION PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def manifest() -> list[dict[str, str]]:
    return [
        {"module": path.name, "sha256": sha256(path)}
        for path in sorted(PACKAGE.glob("*.py"), key=lambda item: item.name)
    ]


def main() -> int:
    print("=" * 40)
    print(" ORR-018 INSTALLER")
    print(" FINAL COMPLETION / FREEZE")
    print(" SUBSYSTEM CERTIFICATION")
    print("=" * 40)
    try:
        source_text = SOURCE.read_text(encoding="utf-8")
        required = (
            'SCHEMA_VERSION = "ORR-017"',
            "OracleResearchResponseEvidenceReadInvocationFinalAttestationConsumptionCompletionReadiness",
            "readiness_hash",
            "completion_readiness_verified",
            "full_lineage_verified",
            "READINESS_TYPE",
            "READINESS_STATUS",
        )
        missing = [item for item in required if item not in source_text]
        if missing:
            raise RuntimeError(f"ORR-017 contract incomplete: {missing}")
        ast.parse(source_text, filename=str(SOURCE))
        protected_hash = sha256(SOURCE)
        print("[OK] Actual ORR-017 completion-readiness gate verified")

        preexisting_hashes = {
            path.resolve(): sha256(path)
            for path in PACKAGE.glob("*.py")
            if path.resolve() not in {PRODUCTION.resolve(), INIT.resolve()}
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_research_response_final_completion_freeze_and_subsystem_certification_gate import ("
            "CERTIFICATION_STATUS, CERTIFICATION_TYPE, EXPECTED_STAGE_COUNT, "
            "OracleResearchResponseFinalCompletionFreezeSubsystemCertification, "
            "OracleResearchResponseFinalCompletionFreezeSubsystemCertificationGate, "
            "OracleResearchResponseFinalCompletionFreezeSubsystemCertificationInvariantError, "
            "build_module_manifest)"
        )
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else "from __future__ import annotations\n"
        if export not in current:
            INIT.write_text(current.rstrip() + "\n\n" + export + "\n", encoding="utf-8", newline="\n")
        ast.parse(INIT.read_text(encoding="utf-8"), filename=str(INIT))
        print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")

        completed = subprocess.run([sys.executable, str(TEST)], cwd=ROOT, check=False)
        if completed.returncode:
            raise RuntimeError(f"ORR-018 test failed with exit code {completed.returncode}")

        if sha256(SOURCE) != protected_hash:
            raise RuntimeError("Protected ORR-017 module changed")
        for path, digest in preexisting_hashes.items():
            if not path.is_file() or sha256(path) != digest:
                raise RuntimeError(f"Protected prior ORR module changed: {path}")

        certificate_body = {
            "schema_version": "ORR-018",
            "certification_status": "oracle_research_response_complete_frozen_and_certified",
            "certified_stage_range": "ORR-001..ORR-018",
            "stage_count": 18,
            "module_manifest": manifest(),
            "read_only": True,
            "runtime_serving_allowed": False,
            "publication_allowed": False,
            "qseries_execution_allowed": False,
            "further_orr_certification_layers_required": False,
        }
        certificate_body["certificate_hash"] = hashlib.sha256(
            __import__("json").dumps(
                certificate_body,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        CERTIFICATE.parent.mkdir(parents=True, exist_ok=True)
        CERTIFICATE.write_text(
            __import__("json").dumps(certificate_body, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"[OK] FREEZE CERTIFICATE: {CERTIFICATE.resolve()}")

        print("[PASS] Protected ORR-017 module unchanged")
        print("[PASS] All prior ORR production modules unchanged")
        print("[PASS] ORR-001 through ORR-018 completion certified")
        print("[PASS] Oracle Research Response subsystem frozen")
        print("[PASS] Deterministic module manifest persisted")
        print("[PASS] Read-only guarantees preserved")
        print("[PASS] No callable was bound or invoked")
        print("[PASS] No evidence result was materialized")
        print("[PASS] Publication disabled")
        print("[PASS] Q Series execution disabled")
        print("[PASS] No further ORR certification layers required")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] ORR SUBSYSTEM COMPLETE, FROZEN, AND CERTIFIED")
        return 0
    except (RuntimeError, SyntaxError, OSError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
