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
            / "oracle_real_intelligence_input_binding_authorization_gate.py"
        )
        test = (
            candidate
            / "test_oit_034_oracle_real_intelligence_input_binding_authorization_gate.py"
        )
        if production.is_file() and test.is_file():
            return candidate

    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_034 = (
    PACKAGE
    / "oracle_real_intelligence_input_binding_authorization_gate.py"
)
OIT_034_TEST = (
    ROOT
    / "test_oit_034_oracle_real_intelligence_input_binding_authorization_gate.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_authorized_real_intelligence_read_session_activation_gate.py"
)
TEST = (
    ROOT
    / "test_oit_035_oracle_authorized_real_intelligence_read_session_activation_gate.py"
)
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport importlib\nimport inspect\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_real_intelligence_input_binding_authorization_gate import (\n    OracleAuthorizedArtifact,\n    OracleAuthorizedCallable,\n    OracleRealIntelligenceAuthorizationInvariantError,\n    OracleRealIntelligenceAuthorizationReport,\n    build_real_intelligence_binding_authorization_report,\n    verify_real_intelligence_binding_authorization_report,\n)\n\nSCHEMA_VERSION = "OIT-035"\nENGINE_ID = "OIT-035"\nPOLICY_ID = "oracle.authorized-real-intelligence-read-session-activation.v1"\n\n\nclass OracleRealIntelligenceReadSessionInvariantError(\n    OracleRealIntelligenceAuthorizationInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleRealIntelligenceArtifactReadReceipt:\n    relative_path: str\n    resolved_path: str\n    expected_byte_count: int\n    observed_byte_count: int\n    expected_sha256: str\n    observed_sha256: str\n    opened_read_only: bool\n    content_loaded: bool\n    content_mutated: bool\n    identity_verified: bool\n    receipt_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleRealIntelligenceCallableResolution:\n    module_name: str\n    callable_name: str\n    expected_signature: tuple[str, ...]\n    observed_signature: tuple[str, ...]\n    module_imported: bool\n    callable_resolved: bool\n    signature_verified: bool\n    callable_invoked: bool\n    resolution_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleRealIntelligenceReadSession:\n    session_id: str\n    authorization_report_hash: str\n    artifact_authorization_hash: str\n    callable_authorization_hash: str\n    artifact_read_receipt: OracleRealIntelligenceArtifactReadReceipt\n    callable_resolution: OracleRealIntelligenceCallableResolution\n    artifact_content_sha256: str\n    artifact_content_byte_count: int\n    session_active: bool\n    bounded_single_artifact: bool\n    read_only: bool\n    analytics_execution_performed: bool\n    callable_invocation_performed: bool\n    database_access_performed: bool\n    runtime_artifact_created: bool\n    runtime_artifact_modified: bool\n    networking_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    session_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleRealIntelligenceReadSessionActivationReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    authorization_report_hash: str\n    read_session: OracleRealIntelligenceReadSession\n    artifact_identity_verified: bool\n    callable_identity_verified: bool\n    callable_signature_verified: bool\n    read_session_active: bool\n    consumption_invocation_ready: bool\n    read_only: bool\n    analytics_execution_performed: bool\n    callable_invocation_performed: bool\n    database_access_performed: bool\n    runtime_artifact_created: bool\n    runtime_artifact_modified: bool\n    networking_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _sha256_bytes(data: bytes) -> str:\n    return hashlib.sha256(data).hexdigest()\n\n\ndef _resolve_authorized_path(\n    repository_root: Path,\n    artifact: OracleAuthorizedArtifact,\n) -> Path:\n    candidate = (repository_root / artifact.relative_path).resolve()\n    runtime_root = (repository_root / "runtime" / "oracle_intelligence").resolve()\n    try:\n        candidate.relative_to(runtime_root)\n    except ValueError as exc:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "authorized artifact escapes canonical runtime root"\n        ) from exc\n    return candidate\n\n\ndef _read_authorized_artifact(\n    repository_root: Path,\n    artifact: OracleAuthorizedArtifact,\n) -> tuple[OracleRealIntelligenceArtifactReadReceipt, bytes]:\n    path = _resolve_authorized_path(repository_root, artifact)\n    if not path.is_file():\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            f"authorized artifact missing: {path}"\n        )\n\n    before_stat = path.stat()\n    with path.open("rb") as handle:\n        content = handle.read()\n    after_stat = path.stat()\n\n    observed_sha = _sha256_bytes(content)\n    observed_count = len(content)\n    unchanged = bool(\n        before_stat.st_size == after_stat.st_size\n        and before_stat.st_mtime_ns == after_stat.st_mtime_ns\n    )\n    identity_verified = bool(\n        observed_count == artifact.byte_count\n        and observed_sha == artifact.sha256\n        and unchanged\n    )\n\n    body = {\n        "relative_path": artifact.relative_path,\n        "resolved_path": str(path),\n        "expected_byte_count": artifact.byte_count,\n        "observed_byte_count": observed_count,\n        "expected_sha256": artifact.sha256,\n        "observed_sha256": observed_sha,\n        "opened_read_only": True,\n        "content_loaded": True,\n        "content_mutated": not unchanged,\n        "identity_verified": identity_verified,\n    }\n    receipt = OracleRealIntelligenceArtifactReadReceipt(\n        **body,\n        receipt_hash=_stable_hash(body),\n    )\n    verify_artifact_read_receipt(receipt)\n    return receipt, content\n\n\ndef _resolve_authorized_callable(\n    authorization: OracleAuthorizedCallable,\n) -> OracleRealIntelligenceCallableResolution:\n    module_imported = False\n    callable_resolved = False\n    observed_signature: tuple[str, ...] = ()\n    resolved = None\n\n    try:\n        module = importlib.import_module(authorization.module_name)\n        module_imported = True\n        resolved = getattr(module, authorization.callable_name)\n        callable_resolved = callable(resolved)\n        if callable_resolved:\n            observed_signature = tuple(\n                inspect.signature(resolved).parameters\n            )\n    except Exception:\n        module_imported = False\n        callable_resolved = False\n        observed_signature = ()\n\n    signature_verified = bool(\n        callable_resolved\n        and observed_signature == tuple(authorization.signature)\n    )\n    body = {\n        "module_name": authorization.module_name,\n        "callable_name": authorization.callable_name,\n        "expected_signature": tuple(authorization.signature),\n        "observed_signature": observed_signature,\n        "module_imported": module_imported,\n        "callable_resolved": callable_resolved,\n        "signature_verified": signature_verified,\n        "callable_invoked": False,\n    }\n    resolution = OracleRealIntelligenceCallableResolution(\n        **body,\n        resolution_hash=_stable_hash(body),\n    )\n    verify_callable_resolution(resolution)\n    return resolution\n\n\ndef verify_artifact_read_receipt(\n    receipt: OracleRealIntelligenceArtifactReadReceipt,\n) -> bool:\n    body = asdict(receipt)\n    supplied = body.pop("receipt_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "artifact read receipt hash mismatch"\n        )\n    if not receipt.opened_read_only or not receipt.content_loaded:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "artifact was not loaded through read-only boundary"\n        )\n    if receipt.content_mutated:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "artifact mutation detected during read"\n        )\n    expected = bool(\n        receipt.expected_byte_count == receipt.observed_byte_count\n        and receipt.expected_sha256 == receipt.observed_sha256\n    )\n    if receipt.identity_verified != expected:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "artifact identity verification mismatch"\n        )\n    return True\n\n\ndef verify_callable_resolution(\n    resolution: OracleRealIntelligenceCallableResolution,\n) -> bool:\n    body = asdict(resolution)\n    supplied = body.pop("resolution_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "callable resolution hash mismatch"\n        )\n    if resolution.callable_invoked:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "callable invocation performed during resolution"\n        )\n    expected = bool(\n        resolution.module_imported\n        and resolution.callable_resolved\n        and resolution.expected_signature == resolution.observed_signature\n    )\n    if resolution.signature_verified != expected:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "callable signature verification mismatch"\n        )\n    return True\n\n\ndef activate_authorized_real_intelligence_read_session(\n    repository_root: str | Path,\n    *,\n    authorization_report: OracleRealIntelligenceAuthorizationReport | None = None,\n) -> OracleRealIntelligenceReadSessionActivationReport:\n    root = Path(repository_root).resolve()\n    source = authorization_report\n    if source is None:\n        source = build_real_intelligence_binding_authorization_report(root)\n    verify_real_intelligence_binding_authorization_report(source)\n\n    if not source.real_input_binding_authorized:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            source.failure_reason or "real input binding not authorized"\n        )\n    if source.authorized_artifact is None:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "authorized artifact missing"\n        )\n    if source.authorized_callable is None:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "authorized callable missing"\n        )\n\n    receipt, content = _read_authorized_artifact(\n        root,\n        source.authorized_artifact,\n    )\n    resolution = _resolve_authorized_callable(\n        source.authorized_callable,\n    )\n\n    active = bool(\n        receipt.identity_verified\n        and resolution.signature_verified\n        and not receipt.content_mutated\n        and not resolution.callable_invoked\n    )\n    session_body = {\n        "session_id": _stable_hash(\n            {\n                "authorization_report_hash": source.report_hash,\n                "artifact_receipt_hash": receipt.receipt_hash,\n                "callable_resolution_hash": resolution.resolution_hash,\n            }\n        )[:24],\n        "authorization_report_hash": source.report_hash,\n        "artifact_authorization_hash": (\n            source.authorized_artifact.authorization_hash\n        ),\n        "callable_authorization_hash": (\n            source.authorized_callable.authorization_hash\n        ),\n        "artifact_read_receipt": receipt,\n        "callable_resolution": resolution,\n        "artifact_content_sha256": _sha256_bytes(content),\n        "artifact_content_byte_count": len(content),\n        "session_active": active,\n        "bounded_single_artifact": True,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "callable_invocation_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n    }\n    session = OracleRealIntelligenceReadSession(\n        **session_body,\n        session_hash=_stable_hash(session_body),\n    )\n    verify_read_session(session)\n\n    report_body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "authorization_report_hash": source.report_hash,\n        "read_session": session,\n        "artifact_identity_verified": receipt.identity_verified,\n        "callable_identity_verified": bool(\n            resolution.module_imported and resolution.callable_resolved\n        ),\n        "callable_signature_verified": resolution.signature_verified,\n        "read_session_active": session.session_active,\n        "consumption_invocation_ready": active,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "callable_invocation_performed": False,\n        "database_access_performed": False,\n        "runtime_artifact_created": False,\n        "runtime_artifact_modified": False,\n        "networking_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None if active else "read_session_not_active",\n    }\n    report = OracleRealIntelligenceReadSessionActivationReport(\n        **report_body,\n        report_hash=_stable_hash(report_body),\n    )\n    verify_read_session_activation_report(report)\n    return report\n\n\ndef verify_read_session(\n    session: OracleRealIntelligenceReadSession,\n) -> bool:\n    body = asdict(session)\n    supplied = body.pop("session_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "read session hash mismatch"\n        )\n    verify_artifact_read_receipt(session.artifact_read_receipt)\n    verify_callable_resolution(session.callable_resolution)\n    if not session.bounded_single_artifact or not session.read_only:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "read session boundary invalid"\n        )\n    if (\n        session.analytics_execution_performed\n        or session.callable_invocation_performed\n        or session.database_access_performed\n        or session.runtime_artifact_created\n        or session.runtime_artifact_modified\n        or session.networking_performed\n        or session.publication_allowed\n        or session.action_authorization_allowed\n        or session.qseries_execution_allowed\n    ):\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "forbidden session capability enabled"\n        )\n    expected = bool(\n        session.artifact_read_receipt.identity_verified\n        and session.callable_resolution.signature_verified\n    )\n    if session.session_active != expected:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "read session activation mismatch"\n        )\n    return True\n\n\ndef verify_read_session_activation_report(\n    report: OracleRealIntelligenceReadSessionActivationReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "read session activation report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "schema mismatch"\n        )\n    if report.policy_id != POLICY_ID:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "policy mismatch"\n        )\n    verify_read_session(report.read_session)\n    if not report.read_only:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "activation report is not read-only"\n        )\n    if (\n        report.analytics_execution_performed\n        or report.callable_invocation_performed\n        or report.database_access_performed\n        or report.runtime_artifact_created\n        or report.runtime_artifact_modified\n        or report.networking_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "forbidden activation capability enabled"\n        )\n    expected = bool(\n        report.artifact_identity_verified\n        and report.callable_identity_verified\n        and report.callable_signature_verified\n        and report.read_session_active\n    )\n    if report.consumption_invocation_ready != expected:\n        raise OracleRealIntelligenceReadSessionInvariantError(\n            "consumption invocation readiness mismatch"\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport sys\nimport types\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_real_intelligence_input_binding_authorization_gate import (\n    ENGINE_ID as OIT_034_ENGINE_ID,\n    POLICY_ID as OIT_034_POLICY_ID,\n    SCHEMA_VERSION as OIT_034_SCHEMA_VERSION,\n    OracleAuthorizedArtifact,\n    OracleAuthorizedCallable,\n    OracleRealIntelligenceAuthorizationReport,\n    _hash as oit_034_hash,\n    verify_real_intelligence_binding_authorization_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_authorized_real_intelligence_read_session_activation_gate import (\n    OracleRealIntelligenceReadSessionInvariantError,\n    activate_authorized_real_intelligence_read_session,\n    verify_read_session_activation_report,\n)\n\n\ndef make_authorization(root: Path, module_name: str):\n    artifact_path = root / "runtime" / "oracle_intelligence" / "real.json"\n    artifact_path.parent.mkdir(parents=True)\n    content = b\'{"record_id":"REAL-035","probability":0.64}\'\n    artifact_path.write_bytes(content)\n\n    artifact_body = {\n        "relative_path": "runtime/oracle_intelligence/real.json",\n        "byte_count": len(content),\n        "sha256": hashlib.sha256(content).hexdigest(),\n        "source_candidate_hash": "artifact-candidate-hash",\n        "authorization_granted": True,\n    }\n    artifact = OracleAuthorizedArtifact(\n        **artifact_body,\n        authorization_hash=oit_034_hash(artifact_body),\n    )\n\n    callable_body = {\n        "module_name": module_name,\n        "callable_name": "load_real_intelligence",\n        "signature": ("repository_root", "artifact_path"),\n        "source_candidate_hash": "callable-candidate-hash",\n        "authorization_granted": True,\n    }\n    callable_item = OracleAuthorizedCallable(\n        **callable_body,\n        authorization_hash=oit_034_hash(callable_body),\n    )\n\n    report_body = {\n        "schema_version": OIT_034_SCHEMA_VERSION,\n        "engine_id": OIT_034_ENGINE_ID,\n        "policy_id": OIT_034_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "readiness_report_hash": "readiness-report-hash",\n        "authorized_artifact": artifact,\n        "authorized_callable": callable_item,\n        "exact_artifact_hash_required": True,\n        "exact_artifact_byte_count_required": True,\n        "read_only_invocation_required": True,\n        "lower_level_bypass_allowed": False,\n        "persistence_allowed": False,\n        "analytics_execution_allowed": False,\n        "database_access_allowed": False,\n        "networking_allowed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "real_input_binding_authorized": True,\n        "read_only": True,\n        "failure_reason": None,\n    }\n    report = OracleRealIntelligenceAuthorizationReport(\n        **report_body,\n        report_hash=oit_034_hash(report_body),\n    )\n    verify_real_intelligence_binding_authorization_report(report)\n    return report, artifact_path\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-035 TEST")\n    print(" AUTHORIZED REAL INTELLIGENCE READ SESSION")\n    print("=" * 48)\n\n    module_name = "oit_035_test_read_callable"\n    module = types.ModuleType(module_name)\n\n    def load_real_intelligence(repository_root, artifact_path):\n        raise AssertionError("callable must not be invoked in OIT-035")\n\n    module.load_real_intelligence = load_real_intelligence\n    sys.modules[module_name] = module\n\n    try:\n        with TemporaryDirectory() as temporary:\n            root = Path(temporary)\n            authorization, artifact_path = make_authorization(\n                root,\n                module_name,\n            )\n            before = artifact_path.read_bytes()\n            before_mtime = artifact_path.stat().st_mtime_ns\n\n            report = activate_authorized_real_intelligence_read_session(\n                root,\n                authorization_report=authorization,\n            )\n\n            assert report.artifact_identity_verified\n            assert report.callable_identity_verified\n            assert report.callable_signature_verified\n            assert report.read_session_active\n            assert report.consumption_invocation_ready\n            assert report.read_session.bounded_single_artifact\n            assert report.read_session.artifact_content_byte_count == len(before)\n            assert report.read_session.artifact_content_sha256 == (\n                hashlib.sha256(before).hexdigest()\n            )\n            assert report.read_session.artifact_read_receipt.opened_read_only\n            assert not report.read_session.artifact_read_receipt.content_mutated\n            assert not report.read_session.callable_resolution.callable_invoked\n\n            assert artifact_path.read_bytes() == before\n            assert artifact_path.stat().st_mtime_ns == before_mtime\n\n            assert not report.analytics_execution_performed\n            assert not report.callable_invocation_performed\n            assert not report.database_access_performed\n            assert not report.runtime_artifact_created\n            assert not report.runtime_artifact_modified\n            assert not report.networking_performed\n            assert not report.publication_allowed\n            assert not report.action_authorization_allowed\n            assert not report.qseries_execution_allowed\n\n            replay = activate_authorized_real_intelligence_read_session(\n                root,\n                authorization_report=authorization,\n            )\n            assert replay == report\n            assert verify_read_session_activation_report(report)\n\n            tampered = replace(\n                report,\n                callable_invocation_performed=True,\n            )\n            try:\n                verify_read_session_activation_report(tampered)\n            except OracleRealIntelligenceReadSessionInvariantError:\n                pass\n            else:\n                raise AssertionError(\n                    "tampered read-session report accepted"\n                )\n\n        print("[PASS] Certified OIT-034 authorization consumed")\n        print("[PASS] Exact authorized artifact reopened read-only")\n        print("[PASS] Artifact SHA-256 reverified")\n        print("[PASS] Artifact byte count reverified")\n        print("[PASS] Artifact bytes and modification time unchanged")\n        print("[PASS] Exact authorized callable resolved")\n        print("[PASS] Callable signature verified")\n        print("[PASS] Callable remained uninvoked")\n        print("[PASS] Bounded single-artifact read session activated")\n        print("[PASS] Read session deterministic across replay")\n        print("[PASS] Tampered read-session report rejected")\n        print("[PASS] No analytics execution or database access performed")\n        print("[PASS] No runtime artifact created or modified")\n        print("[PASS] Publication, action authorization, and Q Series execution disabled")\n        print("[DONE] OIT-035 AUTHORIZED REAL INTELLIGENCE READ SESSION PASS")\n        return 0\n    finally:\n        sys.modules.pop(module_name, None)\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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

    for path in (OIT_034, OIT_034_TEST, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-035 INSTALLER")
    print(" AUTHORIZED REAL INTELLIGENCE READ SESSION")
    print("=" * 48)

    try:
        require_contract(
            OIT_034,
            (
                'SCHEMA_VERSION = "OIT-034"',
                'POLICY_ID = "oracle.real-intelligence-input-binding-authorization.v1"',
                "OracleAuthorizedArtifact",
                "OracleAuthorizedCallable",
                "OracleRealIntelligenceAuthorizationReport",
                "build_real_intelligence_binding_authorization_report",
                "verify_real_intelligence_binding_authorization_report",
                "real_input_binding_authorized",
                "exact_artifact_hash_required",
                "read_only_invocation_required",
            ),
            "Certified OIT-034 production",
        )
        require_contract(
            OIT_034_TEST,
            (
                "OIT-034 TEST",
                "REAL INTELLIGENCE INPUT BINDING AUTHORIZATION",
                "OIT-034 REAL INTELLIGENCE INPUT BINDING AUTHORIZATION PASS",
            ),
            "Certified OIT-034 standalone test",
        )

        protected = protected_sources()

        print("[OK] Certified OIT-034 production contract verified")
        print("[OK] Certified OIT-034 standalone test verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_034_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-034 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_authorized_real_intelligence_read_session_activation_gate import *"
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
                f"OIT-035 test failed with exit code {completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-034 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OIT-035 production module installed")
        print("[PASS] OIT-035 standalone test installed")
        print("[PASS] Exact artifact read-only reopening certified")
        print("[PASS] SHA-256 and byte-count revalidation certified")
        print("[PASS] Exact callable resolution and signature certification installed")
        print("[PASS] Callable invocation remained disabled")
        print("[PASS] No analytics execution or runtime mutation performed")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-035 AUTHORIZED REAL INTELLIGENCE READ SESSION INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
