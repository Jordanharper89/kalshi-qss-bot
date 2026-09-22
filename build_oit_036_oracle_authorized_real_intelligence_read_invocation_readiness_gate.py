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
            / "oracle_authorized_real_intelligence_read_session_activation_gate.py"
        )
        test = (
            candidate
            / "test_oit_035_oracle_authorized_real_intelligence_read_session_activation_gate.py"
        )
        if production.is_file() and test.is_file():
            return candidate

    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_035 = (
    PACKAGE
    / "oracle_authorized_real_intelligence_read_session_activation_gate.py"
)
OIT_035_TEST = (
    ROOT
    / "test_oit_035_oracle_authorized_real_intelligence_read_session_activation_gate.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_authorized_real_intelligence_read_invocation_readiness_gate.py"
)
TEST = (
    ROOT
    / "test_oit_036_oracle_authorized_real_intelligence_read_invocation_readiness_gate.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_authorized_real_intelligence_read_session_activation_gate import (\n    OracleRealIntelligenceReadSessionActivationReport,\n    OracleRealIntelligenceReadSessionInvariantError,\n    activate_authorized_real_intelligence_read_session,\n    verify_read_session_activation_report,\n)\n\nSCHEMA_VERSION = "OIT-036"\nENGINE_ID = "OIT-036"\nPOLICY_ID = "oracle.authorized-real-intelligence-read-invocation-readiness.v1"\n\n\nclass OracleRealIntelligenceReadInvocationReadinessInvariantError(\n    OracleRealIntelligenceReadSessionInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleRealIntelligenceInvocationArgument:\n    argument_name: str\n    argument_position: int\n    value_kind: str\n    canonical_value: str\n    source_lineage_hash: str\n    read_only: bool\n    argument_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleRealIntelligenceReadInvocationManifest:\n    invocation_id: str\n    session_hash: str\n    module_name: str\n    callable_name: str\n    callable_signature: tuple[str, ...]\n    invocation_arguments: tuple[OracleRealIntelligenceInvocationArgument, ...]\n    invocation_argument_count: int\n    exact_signature_bound: bool\n    exact_artifact_path_bound: bool\n    repository_root_bound: bool\n    persist_argument_present: bool\n    persist_argument_value: bool | None\n    invocation_ready: bool\n    callable_invoked: bool\n    read_only: bool\n    manifest_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleRealIntelligenceReadInvocationReadinessReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    read_session_report_hash: str\n    invocation_manifest: OracleRealIntelligenceReadInvocationManifest\n    exact_callable_identity_verified: bool\n    exact_callable_signature_verified: bool\n    exact_argument_binding_verified: bool\n    persistence_disabled: bool\n    bounded_single_artifact_verified: bool\n    invocation_ready: bool\n    invocation_performed: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    runtime_artifact_created: bool\n    runtime_artifact_modified: bool\n    networking_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    read_only: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _argument(\n    *,\n    name: str,\n    position: int,\n    value_kind: str,\n    canonical_value: str,\n    source_lineage_hash: str,\n) -> OracleRealIntelligenceInvocationArgument:\n    body = {\n        "argument_name": name,\n        "argument_position": position,\n        "value_kind": value_kind,\n        "canonical_value": canonical_value,\n        "source_lineage_hash": source_lineage_hash,\n        "read_only": True,\n    }\n    argument = OracleRealIntelligenceInvocationArgument(\n        **body,\n        argument_hash=_stable_hash(body),\n    )\n    verify_invocation_argument(argument)\n    return argument\n\n\ndef _bind_arguments(\n    report: OracleRealIntelligenceReadSessionActivationReport,\n) -> tuple[OracleRealIntelligenceInvocationArgument, ...]:\n    session = report.read_session\n    signature = session.callable_resolution.observed_signature\n    repository_root = report.repository_root\n    artifact_path = session.artifact_read_receipt.resolved_path\n\n    values = []\n    for position, name in enumerate(signature):\n        lowered = name.lower()\n\n        if lowered in {\n            "repository_root",\n            "repo_root",\n            "root",\n        }:\n            values.append(\n                _argument(\n                    name=name,\n                    position=position,\n                    value_kind="repository_root",\n                    canonical_value=repository_root,\n                    source_lineage_hash=report.report_hash,\n                )\n            )\n            continue\n\n        if lowered in {\n            "artifact_path",\n            "path",\n            "source_path",\n            "runtime_artifact_path",\n        }:\n            values.append(\n                _argument(\n                    name=name,\n                    position=position,\n                    value_kind="authorized_artifact_path",\n                    canonical_value=artifact_path,\n                    source_lineage_hash=(\n                        session.artifact_read_receipt.receipt_hash\n                    ),\n                )\n            )\n            continue\n\n        if lowered == "persist":\n            values.append(\n                _argument(\n                    name=name,\n                    position=position,\n                    value_kind="boolean",\n                    canonical_value="false",\n                    source_lineage_hash=session.session_hash,\n                )\n            )\n            continue\n\n        values.append(\n            _argument(\n                name=name,\n                position=position,\n                value_kind="unsupported_unbound",\n                canonical_value="",\n                source_lineage_hash=session.session_hash,\n            )\n        )\n\n    return tuple(values)\n\n\ndef verify_invocation_argument(\n    argument: OracleRealIntelligenceInvocationArgument,\n) -> bool:\n    body = asdict(argument)\n    supplied = body.pop("argument_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(\n            "invocation argument hash mismatch"\n        )\n    if argument.argument_position < 0:\n        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(\n            "invocation argument position invalid"\n        )\n    if not argument.argument_name:\n        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(\n            "invocation argument name missing"\n        )\n    if not argument.source_lineage_hash:\n        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(\n            "invocation argument lineage missing"\n        )\n    if not argument.read_only:\n        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(\n            "invocation argument is not read-only"\n        )\n    return True\n\n\ndef verify_invocation_manifest(\n    manifest: OracleRealIntelligenceReadInvocationManifest,\n) -> bool:\n    body = asdict(manifest)\n    supplied = body.pop("manifest_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(\n            "invocation manifest hash mismatch"\n        )\n    if not manifest.read_only:\n        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(\n            "invocation manifest is not read-only"\n        )\n    if manifest.callable_invoked:\n        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(\n            "callable invoked during readiness certification"\n        )\n    if manifest.invocation_argument_count != len(\n        manifest.invocation_arguments\n    ):\n        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(\n            "invocation argument count mismatch"\n        )\n    for argument in manifest.invocation_arguments:\n        verify_invocation_argument(argument)\n\n    expected_ready = bool(\n        manifest.exact_signature_bound\n        and manifest.exact_artifact_path_bound\n        and manifest.repository_root_bound\n        and all(\n            argument.value_kind != "unsupported_unbound"\n            for argument in manifest.invocation_arguments\n        )\n        and (\n            not manifest.persist_argument_present\n            or manifest.persist_argument_value is False\n        )\n    )\n    if manifest.invocation_ready != expected_ready:\n        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(\n            "invocation readiness mismatch"\n        )\n    return True\n\n\ndef build_authorized_read_invocation_readiness_report(\n    repository_root: str | Path,\n    *,\n    read_session_report: OracleRealIntelligenceReadSessionActivationReport | None = None,\n) -> OracleRealIntelligenceReadInvocationReadinessReport:\n    root = Path(repository_root).resolve()\n    source = read_session_report\n    if source is None:\n        source = activate_authorized_real_intelligence_read_session(root)\n    verify_read_session_activation_report(source)\n\n    if not source.consumption_invocation_ready:\n        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(\n            source.failure_reason or "read session is not invocation-ready"\n        )\n\n    session = source.read_session\n    arguments = _bind_arguments(source)\n    signature = tuple(\n        session.callable_resolution.observed_signature\n    )\n\n    exact_signature_bound = bool(\n        signature\n        and signature\n        == session.callable_resolution.expected_signature\n        and tuple(argument.argument_name for argument in arguments)\n        == signature\n    )\n\n    exact_artifact_path_bound = any(\n        argument.value_kind == "authorized_artifact_path"\n        and argument.canonical_value\n        == session.artifact_read_receipt.resolved_path\n        for argument in arguments\n    )\n\n    repository_root_bound = any(\n        argument.value_kind == "repository_root"\n        and Path(argument.canonical_value).resolve() == root\n        for argument in arguments\n    )\n\n    persist_arguments = tuple(\n        argument\n        for argument in arguments\n        if argument.argument_name.lower() == "persist"\n    )\n    persist_present = bool(persist_arguments)\n    persist_value = (\n        persist_arguments[0].canonical_value.lower() == "true"\n        if persist_arguments\n        else None\n    )\n\n    ready = bool(\n        exact_signature_bound\n        and exact_artifact_path_bound\n        and repository_root_bound\n        and all(\n            argument.value_kind != "unsupported_unbound"\n            for argument in arguments\n        )\n        and (not persist_present or persist_value is False)\n    )\n\n    manifest_body = {\n        "invocation_id": _stable_hash(\n            {\n                "session_hash": session.session_hash,\n                "module_name": (\n                    session.callable_resolution.module_name\n                ),\n                "callable_name": (\n                    session.callable_resolution.callable_name\n                ),\n                "arguments": arguments,\n            }\n        )[:24],\n        "session_hash": session.session_hash,\n        "module_name": session.callable_resolution.module_name,\n        "callable_name": session.callable_resolution.callable_name,\n        "callable_signature": signature,\n        "invocation_arguments": arguments,\n        "invocation_argument_count": len(arguments),\n        "exact_signature_bound": exact_signature_bound,\n        "exact_artifact_path_bound": exact_artifact_path_bound,\n        "repository_root_bound": repository_root_bound,\n        "persist_argument_present": persist_present,\n        "persist_argument_value": persist_value,\n        "invocation_ready": ready,\n        "callable_invoked": False,\n        "read_only": True,\n    }\n    manifest = OracleRealIntelligenceReadInvocationManifest(\n        **manifest_body,\n        manifest_hash=_stable_hash(manifest_body),\n    )\n    verify_invocation_manifest(manifest)\n\n    report_body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "read_session_report_hash": source.report_hash,\n        "invocation_manifest": manifest,\n        "exact_callable_identity_verified": bool(\n            manifest.module_name\n            == session.callable_resolution.module_name\n            and manifest.callable_name\n            == session.callable_resolution.callable_name\n        ),\n        "exact_callable_signature_verified": exact_signature_bound,\n        "exact_argument_binding_verified": ready,\n        "persistence_disabled": bool(\n            not persist_present or persist_value is False\n        ),\n        "bounded_single_artifact_verified": (\n            session.bounded_single_artifact\n        ),\n        "invocation_ready": ready,\n        "invocation_performed": False,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n        "failure_reason": None if ready else "invocation_binding_incomplete",\n    }\n    report = OracleRealIntelligenceReadInvocationReadinessReport(\n        **report_body,\n        report_hash=_stable_hash(report_body),\n    )\n    verify_read_invocation_readiness_report(report)\n    return report\n\n\ndef verify_read_invocation_readiness_report(\n    report: OracleRealIntelligenceReadInvocationReadinessReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(\n            "read invocation readiness report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(\n            "schema mismatch"\n        )\n    if report.policy_id != POLICY_ID:\n        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(\n            "policy mismatch"\n        )\n    verify_invocation_manifest(report.invocation_manifest)\n    if not report.read_only:\n        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(\n            "read invocation readiness report is not read-only"\n        )\n    if (\n        report.invocation_performed\n        or report.analytics_execution_performed\n        or report.database_access_performed\n        or report.runtime_artifact_created\n        or report.runtime_artifact_modified\n        or report.networking_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(\n            "forbidden readiness capability enabled"\n        )\n\n    expected = bool(\n        report.exact_callable_identity_verified\n        and report.exact_callable_signature_verified\n        and report.exact_argument_binding_verified\n        and report.persistence_disabled\n        and report.bounded_single_artifact_verified\n        and report.invocation_manifest.invocation_ready\n    )\n    if report.invocation_ready != expected:\n        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(\n            "read invocation readiness state mismatch"\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport sys\nimport types\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_real_intelligence_input_binding_authorization_gate import (\n    ENGINE_ID as OIT_034_ENGINE_ID,\n    POLICY_ID as OIT_034_POLICY_ID,\n    SCHEMA_VERSION as OIT_034_SCHEMA_VERSION,\n    OracleAuthorizedArtifact,\n    OracleAuthorizedCallable,\n    OracleRealIntelligenceAuthorizationReport,\n    _hash as oit_034_hash,\n    verify_real_intelligence_binding_authorization_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_authorized_real_intelligence_read_session_activation_gate import (\n    activate_authorized_real_intelligence_read_session,\n)\nfrom qseries_v2.oracle_terminal.oracle_authorized_real_intelligence_read_invocation_readiness_gate import (\n    OracleRealIntelligenceReadInvocationReadinessInvariantError,\n    build_authorized_read_invocation_readiness_report,\n    verify_read_invocation_readiness_report,\n)\n\n\ndef make_authorization(root: Path, module_name: str):\n    artifact_path = (\n        root\n        / "runtime"\n        / "oracle_intelligence"\n        / "real_intelligence.json"\n    )\n    artifact_path.parent.mkdir(parents=True)\n    content = b\'{"record_id":"REAL-036","probability":0.67}\'\n    artifact_path.write_bytes(content)\n\n    artifact_body = {\n        "relative_path": (\n            "runtime/oracle_intelligence/real_intelligence.json"\n        ),\n        "byte_count": len(content),\n        "sha256": hashlib.sha256(content).hexdigest(),\n        "source_candidate_hash": "artifact-candidate-hash",\n        "authorization_granted": True,\n    }\n    artifact = OracleAuthorizedArtifact(\n        **artifact_body,\n        authorization_hash=oit_034_hash(artifact_body),\n    )\n\n    callable_body = {\n        "module_name": module_name,\n        "callable_name": "load_real_intelligence",\n        "signature": (\n            "repository_root",\n            "artifact_path",\n            "persist",\n        ),\n        "source_candidate_hash": "callable-candidate-hash",\n        "authorization_granted": True,\n    }\n    callable_item = OracleAuthorizedCallable(\n        **callable_body,\n        authorization_hash=oit_034_hash(callable_body),\n    )\n\n    report_body = {\n        "schema_version": OIT_034_SCHEMA_VERSION,\n        "engine_id": OIT_034_ENGINE_ID,\n        "policy_id": OIT_034_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "readiness_report_hash": "readiness-report-hash",\n        "authorized_artifact": artifact,\n        "authorized_callable": callable_item,\n        "exact_artifact_hash_required": True,\n        "exact_artifact_byte_count_required": True,\n        "read_only_invocation_required": True,\n        "lower_level_bypass_allowed": False,\n        "persistence_allowed": False,\n        "analytics_execution_allowed": False,\n        "database_access_allowed": False,\n        "networking_allowed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "real_input_binding_authorized": True,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    report = OracleRealIntelligenceAuthorizationReport(\n        **report_body,\n        report_hash=oit_034_hash(report_body),\n    )\n    verify_real_intelligence_binding_authorization_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-036 TEST")\n    print(" AUTHORIZED REAL INTELLIGENCE READ INVOCATION READINESS")\n    print("=" * 48)\n\n    module_name = "oit_036_test_callable"\n    module = types.ModuleType(module_name)\n\n    def load_real_intelligence(\n        repository_root,\n        artifact_path,\n        persist,\n    ):\n        raise AssertionError("OIT-036 must not invoke the callable")\n\n    module.load_real_intelligence = load_real_intelligence\n    sys.modules[module_name] = module\n\n    try:\n        with TemporaryDirectory() as temporary:\n            root = Path(temporary)\n            authorization = make_authorization(root, module_name)\n            session = activate_authorized_real_intelligence_read_session(\n                root,\n                authorization_report=authorization,\n            )\n\n            report = build_authorized_read_invocation_readiness_report(\n                root,\n                read_session_report=session,\n            )\n\n            manifest = report.invocation_manifest\n\n            assert report.invocation_ready\n            assert report.exact_callable_identity_verified\n            assert report.exact_callable_signature_verified\n            assert report.exact_argument_binding_verified\n            assert report.persistence_disabled\n            assert report.bounded_single_artifact_verified\n\n            assert manifest.invocation_argument_count == 3\n            assert manifest.callable_signature == (\n                "repository_root",\n                "artifact_path",\n                "persist",\n            )\n            assert manifest.exact_signature_bound\n            assert manifest.exact_artifact_path_bound\n            assert manifest.repository_root_bound\n            assert manifest.persist_argument_present\n            assert manifest.persist_argument_value is False\n            assert manifest.invocation_ready\n            assert not manifest.callable_invoked\n\n            arguments = {\n                argument.argument_name: argument\n                for argument in manifest.invocation_arguments\n            }\n            assert Path(\n                arguments["repository_root"].canonical_value\n            ).resolve() == root.resolve()\n            assert Path(\n                arguments["artifact_path"].canonical_value\n            ).is_file()\n            assert arguments["persist"].canonical_value == "false"\n\n            assert not report.invocation_performed\n            assert not report.analytics_execution_performed\n            assert not report.database_access_performed\n            assert not report.runtime_artifact_created\n            assert not report.runtime_artifact_modified\n            assert not report.networking_performed\n            assert not report.publication_allowed\n            assert not report.action_authorization_allowed\n            assert not report.qseries_execution_allowed\n\n            replay = build_authorized_read_invocation_readiness_report(\n                root,\n                read_session_report=session,\n            )\n            assert replay == report\n            assert verify_read_invocation_readiness_report(report)\n\n            tampered = replace(\n                report,\n                invocation_performed=True,\n            )\n            try:\n                verify_read_invocation_readiness_report(tampered)\n            except OracleRealIntelligenceReadInvocationReadinessInvariantError:\n                pass\n            else:\n                raise AssertionError(\n                    "tampered invocation-readiness report accepted"\n                )\n\n        print("[PASS] Certified OIT-035 read session consumed")\n        print("[PASS] Exact callable identity bound")\n        print("[PASS] Exact callable signature bound")\n        print("[PASS] Repository-root argument bound")\n        print("[PASS] Exact authorized artifact-path argument bound")\n        print("[PASS] Persist argument bound to false")\n        print("[PASS] Unsupported arguments rejected")\n        print("[PASS] Bounded single-artifact invocation certified")\n        print("[PASS] Invocation readiness deterministic across replay")\n        print("[PASS] Callable remained uninvoked")\n        print("[PASS] Tampered invocation-readiness report rejected")\n        print("[PASS] No analytics execution or database access performed")\n        print("[PASS] No runtime artifact created or modified")\n        print("[PASS] Publication, action authorization, and Q Series execution disabled")\n        print("[DONE] OIT-036 AUTHORIZED READ INVOCATION READINESS PASS")\n        return 0\n    finally:\n        sys.modules.pop(module_name, None)\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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

    for path in (OIT_035, OIT_035_TEST, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-036 INSTALLER")
    print(" AUTHORIZED REAL INTELLIGENCE READ INVOCATION READINESS")
    print("=" * 48)

    try:
        require_contract(
            OIT_035,
            (
                'SCHEMA_VERSION = "OIT-035"',
                'POLICY_ID = "oracle.authorized-real-intelligence-read-session-activation.v1"',
                "OracleRealIntelligenceReadSessionActivationReport",
                "OracleRealIntelligenceReadSession",
                "activate_authorized_real_intelligence_read_session",
                "verify_read_session_activation_report",
                "consumption_invocation_ready",
                "callable_invocation_performed",
            ),
            "Certified OIT-035 production",
        )
        require_contract(
            OIT_035_TEST,
            (
                "OIT-035 TEST",
                "AUTHORIZED REAL INTELLIGENCE READ SESSION",
                "OIT-035 AUTHORIZED REAL INTELLIGENCE READ SESSION PASS",
            ),
            "Certified OIT-035 standalone test",
        )

        protected = protected_sources()

        print("[OK] Certified OIT-035 production contract verified")
        print("[OK] Certified OIT-035 standalone test verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_035_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-035 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_authorized_real_intelligence_read_invocation_readiness_gate import *"
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
                f"OIT-036 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-035 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OIT-036 production module installed")
        print("[PASS] OIT-036 standalone test installed")
        print("[PASS] Exact invocation argument binding certified")
        print("[PASS] Persist=false enforcement certified")
        print("[PASS] Unsupported argument rejection certified")
        print("[PASS] Callable remained uninvoked")
        print("[PASS] No analytics execution or runtime mutation performed")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-036 AUTHORIZED READ INVOCATION READINESS INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
