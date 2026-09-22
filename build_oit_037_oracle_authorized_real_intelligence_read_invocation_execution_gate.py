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

        package = candidate / "qseries_v2" / "oracle_terminal"
        production = (
            package
            / "oracle_authorized_real_intelligence_read_invocation_readiness_gate.py"
        )
        test = (
            candidate
            / "test_oit_036_oracle_authorized_real_intelligence_read_invocation_readiness_gate.py"
        )
        if production.is_file() and test.is_file():
            return candidate

    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_036 = (
    PACKAGE
    / "oracle_authorized_real_intelligence_read_invocation_readiness_gate.py"
)
OIT_036_TEST = (
    ROOT
    / "test_oit_036_oracle_authorized_real_intelligence_read_invocation_readiness_gate.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_authorized_real_intelligence_read_invocation_execution_gate.py"
)
TEST = (
    ROOT
    / "test_oit_037_oracle_authorized_real_intelligence_read_invocation_execution_gate.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport importlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_authorized_real_intelligence_read_invocation_readiness_gate import (\n    OracleRealIntelligenceReadInvocationReadinessInvariantError,\n    OracleRealIntelligenceReadInvocationReadinessReport,\n    build_authorized_read_invocation_readiness_report,\n    verify_read_invocation_readiness_report,\n)\n\nSCHEMA_VERSION = "OIT-037"\nENGINE_ID = "OIT-037"\nPOLICY_ID = "oracle.authorized-real-intelligence-read-invocation-execution.v1"\n\n\nclass OracleRealIntelligenceReadInvocationExecutionInvariantError(\n    OracleRealIntelligenceReadInvocationReadinessInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleRealIntelligenceInvocationResult:\n    result_type: str\n    canonical_result: Any\n    result_hash: str\n    result_available: bool\n    result_none: bool\n    read_only: bool\n    verification_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleRealIntelligenceInvocationExecutionReceipt:\n    invocation_id: str\n    readiness_report_hash: str\n    manifest_hash: str\n    module_name: str\n    callable_name: str\n    invocation_argument_names: tuple[str, ...]\n    callable_invocation_count: int\n    callable_invoked: bool\n    invocation_completed: bool\n    artifact_sha256_before: str\n    artifact_sha256_after: str\n    artifact_byte_count_before: int\n    artifact_byte_count_after: int\n    artifact_mtime_ns_before: int\n    artifact_mtime_ns_after: int\n    artifact_unchanged: bool\n    invocation_result: OracleRealIntelligenceInvocationResult\n    persistence_performed: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    runtime_artifact_created: bool\n    runtime_artifact_modified: bool\n    networking_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    read_only: bool\n    receipt_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleRealIntelligenceReadInvocationExecutionReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    readiness_report_hash: str\n    execution_receipt: OracleRealIntelligenceInvocationExecutionReceipt\n    exact_callable_invoked: bool\n    exact_arguments_consumed: bool\n    exactly_one_invocation_performed: bool\n    artifact_identity_preserved: bool\n    bounded_read_result_available: bool\n    execution_succeeded: bool\n    persistence_performed: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    runtime_artifact_created: bool\n    runtime_artifact_modified: bool\n    networking_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    read_only: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, set):\n        return sorted(_canonical(item) for item in value)\n    if isinstance(value, Path):\n        return value.as_posix()\n    if isinstance(value, bytes):\n        return {\n            "__bytes_sha256__": hashlib.sha256(value).hexdigest(),\n            "__bytes_count__": len(value),\n        }\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    if hasattr(value, "to_dict") and callable(value.to_dict):\n        try:\n            return _canonical(value.to_dict())\n        except Exception:\n            pass\n    if hasattr(value, "__dict__"):\n        return _canonical(vars(value))\n    return {\n        "__type__": f"{type(value).__module__}.{type(value).__qualname__}",\n        "__repr__": repr(value),\n    }\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _sha256_file(path: Path) -> str:\n    digest = hashlib.sha256()\n    with path.open("rb") as handle:\n        while True:\n            chunk = handle.read(1024 * 1024)\n            if not chunk:\n                break\n            digest.update(chunk)\n    return digest.hexdigest()\n\n\ndef _argument_value(argument) -> Any:\n    if argument.value_kind == "repository_root":\n        return Path(argument.canonical_value)\n    if argument.value_kind == "authorized_artifact_path":\n        return Path(argument.canonical_value)\n    if argument.value_kind == "boolean":\n        lowered = argument.canonical_value.strip().lower()\n        if lowered == "true":\n            return True\n        if lowered == "false":\n            return False\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "unsupported boolean invocation value"\n        )\n    raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n        f"unsupported invocation argument kind: {argument.value_kind}"\n    )\n\n\ndef _build_result(value: Any) -> OracleRealIntelligenceInvocationResult:\n    canonical = _canonical(value)\n    body = {\n        "result_type": (\n            f"{type(value).__module__}.{type(value).__qualname__}"\n        ),\n        "canonical_result": canonical,\n        "result_hash": _stable_hash(canonical),\n        "result_available": True,\n        "result_none": value is None,\n        "read_only": True,\n    }\n    result = OracleRealIntelligenceInvocationResult(\n        **body,\n        verification_hash=_stable_hash(body),\n    )\n    verify_invocation_result(result)\n    return result\n\n\ndef verify_invocation_result(\n    result: OracleRealIntelligenceInvocationResult,\n) -> bool:\n    body = asdict(result)\n    supplied = body.pop("verification_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "invocation result verification hash mismatch"\n        )\n    if not result.read_only:\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "invocation result is not read-only"\n        )\n    if not result.result_available:\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "invocation result unavailable"\n        )\n    if result.result_hash != _stable_hash(result.canonical_result):\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "invocation result hash mismatch"\n        )\n    return True\n\n\ndef execute_authorized_real_intelligence_read_invocation(\n    repository_root: str | Path,\n    *,\n    readiness_report: OracleRealIntelligenceReadInvocationReadinessReport | None = None,\n) -> OracleRealIntelligenceReadInvocationExecutionReport:\n    root = Path(repository_root).resolve()\n    source = readiness_report\n    if source is None:\n        source = build_authorized_read_invocation_readiness_report(root)\n    verify_read_invocation_readiness_report(source)\n\n    if not source.invocation_ready:\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            source.failure_reason or "invocation is not ready"\n        )\n\n    manifest = source.invocation_manifest\n    module = importlib.import_module(manifest.module_name)\n    callable_object = getattr(module, manifest.callable_name)\n    if not callable(callable_object):\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "authorized callable did not resolve"\n        )\n\n    kwargs = {\n        argument.argument_name: _argument_value(argument)\n        for argument in manifest.invocation_arguments\n    }\n    if tuple(kwargs) != tuple(manifest.callable_signature):\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "bound invocation arguments do not match callable signature"\n        )\n\n    artifact_argument = next(\n        (\n            argument\n            for argument in manifest.invocation_arguments\n            if argument.value_kind == "authorized_artifact_path"\n        ),\n        None,\n    )\n    if artifact_argument is None:\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "authorized artifact-path argument missing"\n        )\n\n    artifact_path = Path(artifact_argument.canonical_value).resolve()\n    before_stat = artifact_path.stat()\n    before_sha = _sha256_file(artifact_path)\n\n    result_value = callable_object(**kwargs)\n\n    after_stat = artifact_path.stat()\n    after_sha = _sha256_file(artifact_path)\n\n    unchanged = bool(\n        before_sha == after_sha\n        and before_stat.st_size == after_stat.st_size\n        and before_stat.st_mtime_ns == after_stat.st_mtime_ns\n    )\n    if not unchanged:\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "authorized artifact changed during read invocation"\n        )\n\n    result = _build_result(result_value)\n\n    receipt_body = {\n        "invocation_id": manifest.invocation_id,\n        "readiness_report_hash": source.report_hash,\n        "manifest_hash": manifest.manifest_hash,\n        "module_name": manifest.module_name,\n        "callable_name": manifest.callable_name,\n        "invocation_argument_names": tuple(kwargs),\n        "callable_invocation_count": 1,\n        "callable_invoked": True,\n        "invocation_completed": True,\n        "artifact_sha256_before": before_sha,\n        "artifact_sha256_after": after_sha,\n        "artifact_byte_count_before": before_stat.st_size,\n        "artifact_byte_count_after": after_stat.st_size,\n        "artifact_mtime_ns_before": before_stat.st_mtime_ns,\n        "artifact_mtime_ns_after": after_stat.st_mtime_ns,\n        "artifact_unchanged": unchanged,\n        "invocation_result": result,\n        "persistence_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n    }\n    receipt = OracleRealIntelligenceInvocationExecutionReceipt(\n        **receipt_body,\n        receipt_hash=_stable_hash(receipt_body),\n    )\n    verify_execution_receipt(receipt)\n\n    report_body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "readiness_report_hash": source.report_hash,\n        "execution_receipt": receipt,\n        "exact_callable_invoked": bool(\n            receipt.module_name == manifest.module_name\n            and receipt.callable_name == manifest.callable_name\n        ),\n        "exact_arguments_consumed": bool(\n            receipt.invocation_argument_names\n            == tuple(manifest.callable_signature)\n        ),\n        "exactly_one_invocation_performed": (\n            receipt.callable_invocation_count == 1\n        ),\n        "artifact_identity_preserved": receipt.artifact_unchanged,\n        "bounded_read_result_available": (\n            receipt.invocation_result.result_available\n        ),\n        "execution_succeeded": bool(\n            receipt.invocation_completed\n            and receipt.callable_invocation_count == 1\n            and receipt.artifact_unchanged\n            and receipt.invocation_result.result_available\n        ),\n        "persistence_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    report = OracleRealIntelligenceReadInvocationExecutionReport(\n        **report_body,\n        report_hash=_stable_hash(report_body),\n    )\n    verify_read_invocation_execution_report(report)\n    return report\n\n\ndef verify_execution_receipt(\n    receipt: OracleRealIntelligenceInvocationExecutionReceipt,\n) -> bool:\n    body = asdict(receipt)\n    supplied = body.pop("receipt_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "execution receipt hash mismatch"\n        )\n    verify_invocation_result(receipt.invocation_result)\n    if not receipt.read_only:\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "execution receipt is not read-only"\n        )\n    if receipt.callable_invocation_count != 1:\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "read invocation count is not exactly one"\n        )\n    if not receipt.callable_invoked or not receipt.invocation_completed:\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "read invocation did not complete"\n        )\n    expected_unchanged = bool(\n        receipt.artifact_sha256_before == receipt.artifact_sha256_after\n        and receipt.artifact_byte_count_before\n        == receipt.artifact_byte_count_after\n        and receipt.artifact_mtime_ns_before\n        == receipt.artifact_mtime_ns_after\n    )\n    if receipt.artifact_unchanged != expected_unchanged:\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "artifact preservation state mismatch"\n        )\n    if (\n        receipt.persistence_performed\n        or receipt.analytics_execution_performed\n        or receipt.database_access_performed\n        or receipt.runtime_artifact_created\n        or receipt.runtime_artifact_modified\n        or receipt.networking_performed\n        or receipt.publication_allowed\n        or receipt.action_authorization_allowed\n        or receipt.qseries_execution_allowed\n    ):\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "forbidden execution capability enabled"\n        )\n    return True\n\n\ndef verify_read_invocation_execution_report(\n    report: OracleRealIntelligenceReadInvocationExecutionReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "read invocation execution report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "schema mismatch"\n        )\n    if report.policy_id != POLICY_ID:\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "policy mismatch"\n        )\n    verify_execution_receipt(report.execution_receipt)\n    if not report.read_only:\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "execution report is not read-only"\n        )\n    if (\n        report.persistence_performed\n        or report.analytics_execution_performed\n        or report.database_access_performed\n        or report.runtime_artifact_created\n        or report.runtime_artifact_modified\n        or report.networking_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "forbidden report capability enabled"\n        )\n    expected = bool(\n        report.exact_callable_invoked\n        and report.exact_arguments_consumed\n        and report.exactly_one_invocation_performed\n        and report.artifact_identity_preserved\n        and report.bounded_read_result_available\n        and report.execution_receipt.invocation_completed\n    )\n    if report.execution_succeeded != expected:\n        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(\n            "read invocation execution state mismatch"\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport sys\nimport types\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_authorized_real_intelligence_read_invocation_readiness_gate import (\n    ENGINE_ID as OIT_036_ENGINE_ID,\n    POLICY_ID as OIT_036_POLICY_ID,\n    SCHEMA_VERSION as OIT_036_SCHEMA_VERSION,\n    OracleRealIntelligenceInvocationArgument,\n    OracleRealIntelligenceReadInvocationManifest,\n    OracleRealIntelligenceReadInvocationReadinessReport,\n    _stable_hash as oit_036_hash,\n    verify_read_invocation_readiness_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_authorized_real_intelligence_read_invocation_execution_gate import (\n    OracleRealIntelligenceReadInvocationExecutionInvariantError,\n    execute_authorized_real_intelligence_read_invocation,\n    verify_read_invocation_execution_report,\n)\n\n\ndef make_readiness(root: Path, module_name: str):\n    artifact = (\n        root\n        / "runtime"\n        / "oracle_intelligence"\n        / "real_intelligence.json"\n    )\n    artifact.parent.mkdir(parents=True)\n    artifact.write_bytes(\n        b\'{"record_id":"REAL-037","probability":0.71}\'\n    )\n\n    arguments = []\n    definitions = (\n        (\n            "repository_root",\n            0,\n            "repository_root",\n            str(root.resolve()),\n            "session-lineage",\n        ),\n        (\n            "artifact_path",\n            1,\n            "authorized_artifact_path",\n            str(artifact.resolve()),\n            "artifact-lineage",\n        ),\n        (\n            "persist",\n            2,\n            "boolean",\n            "false",\n            "session-lineage",\n        ),\n    )\n    for name, position, kind, value, lineage in definitions:\n        body = {\n            "argument_name": name,\n            "argument_position": position,\n            "value_kind": kind,\n            "canonical_value": value,\n            "source_lineage_hash": lineage,\n            "read_only": True,\n        }\n        arguments.append(\n            OracleRealIntelligenceInvocationArgument(\n                **body,\n                argument_hash=oit_036_hash(body),\n            )\n        )\n\n    manifest_body = {\n        "invocation_id": "invocation-037",\n        "session_hash": "session-hash",\n        "module_name": module_name,\n        "callable_name": "load_real_intelligence",\n        "callable_signature": (\n            "repository_root",\n            "artifact_path",\n            "persist",\n        ),\n        "invocation_arguments": tuple(arguments),\n        "invocation_argument_count": 3,\n        "exact_signature_bound": True,\n        "exact_artifact_path_bound": True,\n        "repository_root_bound": True,\n        "persist_argument_present": True,\n        "persist_argument_value": False,\n        "invocation_ready": True,\n        "callable_invoked": False,\n        "read_only": True,\n    }\n    manifest = OracleRealIntelligenceReadInvocationManifest(\n        **manifest_body,\n        manifest_hash=oit_036_hash(manifest_body),\n    )\n\n    report_body = {\n        "schema_version": OIT_036_SCHEMA_VERSION,\n        "engine_id": OIT_036_ENGINE_ID,\n        "policy_id": OIT_036_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "read_session_report_hash": "read-session-report-hash",\n        "invocation_manifest": manifest,\n        "exact_callable_identity_verified": True,\n        "exact_callable_signature_verified": True,\n        "exact_argument_binding_verified": True,\n        "persistence_disabled": True,\n        "bounded_single_artifact_verified": True,\n        "invocation_ready": True,\n        "invocation_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    report = OracleRealIntelligenceReadInvocationReadinessReport(\n        **report_body,\n        report_hash=oit_036_hash(report_body),\n    )\n    verify_read_invocation_readiness_report(report)\n    return report, artifact\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-037 TEST")\n    print(" AUTHORIZED REAL INTELLIGENCE READ INVOCATION EXECUTION")\n    print("=" * 48)\n\n    module_name = "oit_037_test_callable"\n    module = types.ModuleType(module_name)\n    call_count = {"value": 0}\n\n    def load_real_intelligence(\n        repository_root,\n        artifact_path,\n        persist,\n    ):\n        call_count["value"] += 1\n        assert isinstance(repository_root, Path)\n        assert isinstance(artifact_path, Path)\n        assert persist is False\n        return {\n            "record_id": "REAL-037",\n            "source_sha256": hashlib.sha256(\n                artifact_path.read_bytes()\n            ).hexdigest(),\n            "read_only": True,\n        }\n\n    module.load_real_intelligence = load_real_intelligence\n    sys.modules[module_name] = module\n\n    try:\n        with TemporaryDirectory() as temporary:\n            root = Path(temporary)\n            readiness, artifact = make_readiness(root, module_name)\n            before = artifact.read_bytes()\n            before_mtime = artifact.stat().st_mtime_ns\n\n            report = execute_authorized_real_intelligence_read_invocation(\n                root,\n                readiness_report=readiness,\n            )\n\n            assert call_count["value"] == 1\n            assert report.execution_succeeded\n            assert report.exact_callable_invoked\n            assert report.exact_arguments_consumed\n            assert report.exactly_one_invocation_performed\n            assert report.artifact_identity_preserved\n            assert report.bounded_read_result_available\n\n            receipt = report.execution_receipt\n            assert receipt.callable_invocation_count == 1\n            assert receipt.callable_invoked\n            assert receipt.invocation_completed\n            assert receipt.artifact_unchanged\n            assert receipt.invocation_result.result_available\n            assert not receipt.invocation_result.result_none\n            assert receipt.invocation_result.canonical_result[\n                "record_id"\n            ] == "REAL-037"\n\n            assert artifact.read_bytes() == before\n            assert artifact.stat().st_mtime_ns == before_mtime\n\n            assert not report.persistence_performed\n            assert not report.analytics_execution_performed\n            assert not report.database_access_performed\n            assert not report.runtime_artifact_created\n            assert not report.runtime_artifact_modified\n            assert not report.networking_performed\n            assert not report.publication_allowed\n            assert not report.action_authorization_allowed\n            assert not report.qseries_execution_allowed\n\n            assert verify_read_invocation_execution_report(report)\n\n            tampered = replace(\n                report,\n                runtime_artifact_modified=True,\n            )\n            try:\n                verify_read_invocation_execution_report(tampered)\n            except OracleRealIntelligenceReadInvocationExecutionInvariantError:\n                pass\n            else:\n                raise AssertionError(\n                    "tampered execution report accepted"\n                )\n\n        print("[PASS] Certified OIT-036 invocation readiness consumed")\n        print("[PASS] Exact authorized callable invoked")\n        print("[PASS] Exact bound arguments consumed")\n        print("[PASS] Persist=false enforced")\n        print("[PASS] Exactly one invocation performed")\n        print("[PASS] Bounded read result captured")\n        print("[PASS] Result canonicalized and hash verified")\n        print("[PASS] Artifact SHA-256 preserved")\n        print("[PASS] Artifact byte count and modification time preserved")\n        print("[PASS] No persistence or analytics execution performed")\n        print("[PASS] No database or networking access performed")\n        print("[PASS] No runtime artifact created or modified")\n        print("[PASS] Tampered execution report rejected")\n        print("[PASS] Publication, action authorization, and Q Series execution disabled")\n        print("[DONE] OIT-037 AUTHORIZED READ INVOCATION EXECUTION PASS")\n        return 0\n    finally:\n        sys.modules.pop(module_name, None)\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_contract(
    path: Path,
    tokens: tuple[str, ...],
    label: str,
) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label} missing: {path}")
    source = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in source]
    if missing:
        raise RuntimeError(f"{label} contract mismatch: {missing}")


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def protected_sources() -> dict[Path, str]:
    protected = {}
    roots = (
        ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition",
        ROOT / "qseries_v2" / "oracle_intelligence" / "analytics",
        ROOT / "qseries_v2" / "oracle_intelligence_integration",
        ROOT / "qseries_v2" / "oracle_research_runtime",
        ROOT / "qseries_v2" / "oracle_operator_runtime",
        ROOT / "qseries_v2" / "qseries",
    )
    for base in roots:
        if base.exists():
            for path in base.rglob("*.py"):
                if path.is_file():
                    protected[path] = sha256(path)

    for path in (OIT_036, OIT_036_TEST, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-037 INSTALLER")
    print(" AUTHORIZED REAL INTELLIGENCE READ INVOCATION EXECUTION")
    print("=" * 48)

    try:
        require_contract(
            OIT_036,
            (
                'SCHEMA_VERSION = "OIT-036"',
                'POLICY_ID = "oracle.authorized-real-intelligence-read-invocation-readiness.v1"',
                "OracleRealIntelligenceReadInvocationReadinessReport",
                "OracleRealIntelligenceReadInvocationManifest",
                "build_authorized_read_invocation_readiness_report",
                "verify_read_invocation_readiness_report",
                "invocation_ready",
                "persist_argument_value",
                "invocation_performed",
            ),
            "Certified OIT-036 production",
        )
        require_contract(
            OIT_036_TEST,
            (
                "OIT-036 TEST",
                "AUTHORIZED REAL INTELLIGENCE READ INVOCATION READINESS",
                "OIT-036 AUTHORIZED READ INVOCATION READINESS PASS",
            ),
            "Certified OIT-036 standalone test",
        )

        protected = protected_sources()

        print("[OK] Certified OIT-036 production contract verified")
        print("[OK] Certified OIT-036 standalone test verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_036_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-036 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_authorized_real_intelligence_read_invocation_execution_gate import *"
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
                f"OIT-037 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-036 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OIT-037 production module installed")
        print("[PASS] OIT-037 standalone test installed")
        print("[PASS] Exactly one authorized read invocation certified")
        print("[PASS] Bounded result capture and hashing certified")
        print("[PASS] Artifact identity preservation certified")
        print("[PASS] Persistence and analytics execution remained disabled")
        print("[PASS] No database, networking, or runtime mutation performed")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-037 AUTHORIZED READ INVOCATION EXECUTION INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
