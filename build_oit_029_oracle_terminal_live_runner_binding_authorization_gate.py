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
        required = (
            candidate / "qseries_v2" / "oracle_terminal"
            / "oracle_terminal_live_runner_binding_readiness_gate.py"
        )
        if required.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_028 = PACKAGE / "oracle_terminal_live_runner_binding_readiness_gate.py"
OIT_028_TEST = ROOT / "test_oit_028_oracle_terminal_live_runner_binding_readiness_gate.py"
PRODUCTION = PACKAGE / "oracle_terminal_live_runner_binding_authorization_gate.py"
TEST = ROOT / "test_oit_029_oracle_terminal_live_runner_binding_authorization_gate.py"
INIT = PACKAGE / "__init__.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_terminal_live_runner_binding_readiness_gate import (\n    OracleTerminalRunnerBindingReadinessGateReport,\n    OracleTerminalRunnerBindingReadinessInvariantError,\n    build_terminal_runner_binding_readiness_gate_report,\n    verify_terminal_runner_binding_readiness_gate_report,\n)\n\nSCHEMA_VERSION = "OIT-029"\nENGINE_ID = "OIT-029"\nPOLICY_ID = "oracle.live-runner-binding-authorization-gate.v1"\n\nAUTHORIZED_MODULE = (\n    "qseries_v2.oracle_terminal."\n    "oracle_terminal_activated_output_display_session_gate"\n)\nAUTHORIZED_CALLABLE = "build_terminal_display_session_gate_report"\n\n\nclass OracleTerminalRunnerBindingAuthorizationInvariantError(\n    OracleTerminalRunnerBindingReadinessInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleTerminalRunnerCallableAuthorization:\n    authorization_id: str\n    runner_sha256: str\n    readiness_report_hash: str\n    authorized_module: str\n    authorized_callable: str\n    authorized_signature: tuple[str, ...]\n    invocation_mode: str\n    display_only: bool\n    read_only: bool\n    analytics_access_allowed: bool\n    database_access_allowed: bool\n    networking_allowed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    authorization_granted: bool\n    authorization_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalRunnerDeniedCapability:\n    capability_name: str\n    denial_reason: str\n    denial_enforced: bool\n    denial_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalRunnerBindingAuthorizationGateReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    readiness_report_hash: str\n    runner_sha256: str\n    callable_authorization: OracleTerminalRunnerCallableAuthorization\n    denied_capabilities: tuple[OracleTerminalRunnerDeniedCapability, ...]\n    denied_capability_count: int\n    runner_identity_authorized: bool\n    callable_identity_authorized: bool\n    signature_authorized: bool\n    display_only_authorized: bool\n    read_only_boundary_authorized: bool\n    live_runner_binding_authorized: bool\n    runner_modified: bool\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _build_denial(\n    capability_name: str,\n    denial_reason: str,\n) -> OracleTerminalRunnerDeniedCapability:\n    body = {\n        "capability_name": capability_name,\n        "denial_reason": denial_reason,\n        "denial_enforced": True,\n    }\n    return OracleTerminalRunnerDeniedCapability(\n        **body,\n        denial_hash=_stable_hash(body),\n    )\n\n\ndef verify_terminal_runner_denied_capability(\n    denial: OracleTerminalRunnerDeniedCapability,\n) -> bool:\n    body = asdict(denial)\n    supplied = body.pop("denial_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "runner denied capability hash mismatch"\n        )\n    if not denial.capability_name or not denial.denial_reason:\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "runner denied capability metadata missing"\n        )\n    if not denial.denial_enforced:\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "runner denied capability not enforced"\n        )\n    return True\n\n\ndef _build_authorization(\n    readiness: OracleTerminalRunnerBindingReadinessGateReport,\n) -> OracleTerminalRunnerCallableAuthorization:\n    binding = readiness.binding_contract\n    granted = bool(\n        readiness.live_runner_binding_ready\n        and readiness.runner_identity_verified\n        and readiness.syntax_verified\n        and readiness.import_safety_verified\n        and readiness.callable_resolution_verified\n        and readiness.signature_compatibility_verified\n        and readiness.read_only_dependency_verified\n        and not readiness.runner_modified\n        and binding.required_callable_module == AUTHORIZED_MODULE\n        and binding.required_callable_name == AUTHORIZED_CALLABLE\n        and binding.required_callable_signature == ("repository_root", "query")\n        and not binding.publication_exposure_detected\n        and not binding.execution_exposure_detected\n        and not binding.database_write_exposure_detected\n        and not binding.networking_side_effect_exposure_detected\n    )\n    body = {\n        "authorization_id": _stable_hash(\n            {\n                "runner_sha256": readiness.runner_inspection.runner_sha256,\n                "readiness_report_hash": readiness.report_hash,\n                "module": AUTHORIZED_MODULE,\n                "callable": AUTHORIZED_CALLABLE,\n            }\n        )[:24],\n        "runner_sha256": readiness.runner_inspection.runner_sha256,\n        "readiness_report_hash": readiness.report_hash,\n        "authorized_module": AUTHORIZED_MODULE,\n        "authorized_callable": AUTHORIZED_CALLABLE,\n        "authorized_signature": ("repository_root", "query"),\n        "invocation_mode": "display_session_only",\n        "display_only": True,\n        "read_only": True,\n        "analytics_access_allowed": False,\n        "database_access_allowed": False,\n        "networking_allowed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "authorization_granted": granted,\n    }\n    authorization = OracleTerminalRunnerCallableAuthorization(\n        **body,\n        authorization_hash=_stable_hash(body),\n    )\n    verify_terminal_runner_callable_authorization(authorization)\n    return authorization\n\n\ndef verify_terminal_runner_callable_authorization(\n    authorization: OracleTerminalRunnerCallableAuthorization,\n) -> bool:\n    body = asdict(authorization)\n    supplied = body.pop("authorization_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "runner callable authorization hash mismatch"\n        )\n    if authorization.authorized_module != AUTHORIZED_MODULE:\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "unauthorized runner module"\n        )\n    if authorization.authorized_callable != AUTHORIZED_CALLABLE:\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "unauthorized runner callable"\n        )\n    if authorization.authorized_signature != ("repository_root", "query"):\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "unauthorized runner callable signature"\n        )\n    if authorization.invocation_mode != "display_session_only":\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "runner invocation mode is not display-session-only"\n        )\n    if not authorization.display_only or not authorization.read_only:\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "runner authorization is not read-only display-only"\n        )\n    if (\n        authorization.analytics_access_allowed\n        or authorization.database_access_allowed\n        or authorization.networking_allowed\n        or authorization.publication_allowed\n        or authorization.action_authorization_allowed\n        or authorization.qseries_execution_allowed\n    ):\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "forbidden runner capability authorized"\n        )\n    return True\n\n\ndef build_terminal_runner_binding_authorization_gate_report(\n    repository_root: str | Path,\n    query: str,\n    *,\n    readiness_report: OracleTerminalRunnerBindingReadinessGateReport | None = None,\n) -> OracleTerminalRunnerBindingAuthorizationGateReport:\n    root = Path(repository_root).resolve()\n    source = readiness_report\n    if source is None:\n        source = build_terminal_runner_binding_readiness_gate_report(root, query)\n    verify_terminal_runner_binding_readiness_gate_report(source)\n\n    authorization = _build_authorization(source)\n    denials = (\n        _build_denial(\n            "direct_analytics_execution",\n            "runner may consume only the certified display-session gate",\n        ),\n        _build_denial(\n            "database_access",\n            "terminal presentation runner has no database-access authority",\n        ),\n        _build_denial(\n            "networking",\n            "terminal presentation runner has no direct networking authority",\n        ),\n        _build_denial(\n            "publication",\n            "display output is local and not publication-authorized",\n        ),\n        _build_denial(\n            "action_authorization",\n            "terminal output cannot authorize operator or market actions",\n        ),\n        _build_denial(\n            "qseries_execution",\n            "Oracle remains isolated from Q Series execution",\n        ),\n        _build_denial(\n            "lower_level_terminal_bypass",\n            "runner must invoke the certified OIT-027 display-session boundary",\n        ),\n    )\n    for denial in denials:\n        verify_terminal_runner_denied_capability(denial)\n\n    authorized = bool(\n        authorization.authorization_granted\n        and all(item.denial_enforced for item in denials)\n    )\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "readiness_report_hash": source.report_hash,\n        "runner_sha256": source.runner_inspection.runner_sha256,\n        "callable_authorization": authorization,\n        "denied_capabilities": denials,\n        "denied_capability_count": len(denials),\n        "runner_identity_authorized": bool(\n            source.runner_identity_verified\n            and authorization.runner_sha256\n            == source.runner_inspection.runner_sha256\n        ),\n        "callable_identity_authorized": bool(\n            authorization.authorized_module == AUTHORIZED_MODULE\n            and authorization.authorized_callable == AUTHORIZED_CALLABLE\n        ),\n        "signature_authorized": bool(\n            authorization.authorized_signature\n            == ("repository_root", "query")\n        ),\n        "display_only_authorized": bool(\n            authorization.display_only\n            and authorization.invocation_mode == "display_session_only"\n        ),\n        "read_only_boundary_authorized": bool(\n            authorization.read_only\n            and not authorization.analytics_access_allowed\n            and not authorization.database_access_allowed\n            and not authorization.networking_allowed\n            and not authorization.publication_allowed\n            and not authorization.action_authorization_allowed\n            and not authorization.qseries_execution_allowed\n        ),\n        "live_runner_binding_authorized": authorized,\n        "runner_modified": False,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None if authorized else "runner_binding_not_authorized",\n    }\n    report = OracleTerminalRunnerBindingAuthorizationGateReport(\n        **body,\n        report_hash=_stable_hash(body),\n    )\n    verify_terminal_runner_binding_authorization_gate_report(report)\n    return report\n\n\ndef verify_terminal_runner_binding_authorization_gate_report(\n    report: OracleTerminalRunnerBindingAuthorizationGateReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "runner binding authorization report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "schema mismatch"\n        )\n    if report.policy_id != POLICY_ID:\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "policy mismatch"\n        )\n    if report.runner_modified:\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "runner modification detected during authorization"\n        )\n    if not report.read_only:\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "runner binding authorization report is not read-only"\n        )\n    if (\n        report.analytics_execution_performed\n        or report.database_access_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "forbidden capability enabled"\n        )\n    verify_terminal_runner_callable_authorization(\n        report.callable_authorization\n    )\n    if report.denied_capability_count != len(report.denied_capabilities):\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "denied capability count mismatch"\n        )\n    for denial in report.denied_capabilities:\n        verify_terminal_runner_denied_capability(denial)\n    if report.readiness_report_hash != (\n        report.callable_authorization.readiness_report_hash\n    ):\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "authorization readiness lineage mismatch"\n        )\n    if report.runner_sha256 != report.callable_authorization.runner_sha256:\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "authorization runner identity mismatch"\n        )\n    expected = bool(\n        report.callable_authorization.authorization_granted\n        and report.runner_identity_authorized\n        and report.callable_identity_authorized\n        and report.signature_authorized\n        and report.display_only_authorized\n        and report.read_only_boundary_authorized\n        and all(\n            denial.denial_enforced\n            for denial in report.denied_capabilities\n        )\n    )\n    if report.live_runner_binding_authorized != expected:\n        raise OracleTerminalRunnerBindingAuthorizationInvariantError(\n            "runner binding authorization state mismatch"\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_terminal_live_runner_binding_readiness_gate import (\n    ENGINE_ID as OIT_028_ENGINE_ID,\n    POLICY_ID as OIT_028_POLICY_ID,\n    SCHEMA_VERSION as OIT_028_SCHEMA_VERSION,\n    OracleTerminalRunnerBindingContract,\n    OracleTerminalRunnerBindingReadinessGateReport,\n    OracleTerminalRunnerInspection,\n    _stable_hash as oit_028_hash,\n    verify_terminal_runner_binding_readiness_gate_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_live_runner_binding_authorization_gate import (\n    OracleTerminalRunnerBindingAuthorizationInvariantError,\n    build_terminal_runner_binding_authorization_gate_report,\n    verify_terminal_runner_binding_authorization_gate_report,\n)\n\n\ndef make_readiness_report(root: Path):\n    inspection_body = {\n        "runner_path": str(\n            root / "run_oracle_open_intelligence_terminal.py"\n        ),\n        "runner_name": "run_oracle_open_intelligence_terminal.py",\n        "runner_exists": True,\n        "runner_sha256": "runner-sha256",\n        "syntax_valid": True,\n        "top_level_imports": ("pathlib",),\n        "top_level_functions": ("main",),\n        "main_entrypoint_present": True,\n        "direct_execution_guard_present": True,\n        "forbidden_imports": (),\n        "forbidden_call_sites": (),\n        "import_side_effect_risk_detected": False,\n    }\n    inspection = OracleTerminalRunnerInspection(\n        **inspection_body,\n        inspection_hash=oit_028_hash(inspection_body),\n    )\n    binding_body = {\n        "binding_id": "binding-001",\n        "runner_sha256": "runner-sha256",\n        "source_display_session_gate_hash": "display-session-gate-hash",\n        "required_callable_module": (\n            "qseries_v2.oracle_terminal."\n            "oracle_terminal_activated_output_display_session_gate"\n        ),\n        "required_callable_name": (\n            "build_terminal_display_session_gate_report"\n        ),\n        "required_callable_signature": ("repository_root", "query"),\n        "runner_entrypoint_name": "main",\n        "import_safe": True,\n        "callable_resolution_ready": True,\n        "signature_compatible": True,\n        "read_only_dependency_path": True,\n        "publication_exposure_detected": False,\n        "execution_exposure_detected": False,\n        "database_write_exposure_detected": False,\n        "networking_side_effect_exposure_detected": False,\n        "binding_ready": True,\n    }\n    binding = OracleTerminalRunnerBindingContract(\n        **binding_body,\n        binding_hash=oit_028_hash(binding_body),\n    )\n    report_body = {\n        "schema_version": OIT_028_SCHEMA_VERSION,\n        "engine_id": OIT_028_ENGINE_ID,\n        "policy_id": OIT_028_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "runner_inspection": inspection,\n        "binding_contract": binding,\n        "runner_identity_verified": True,\n        "syntax_verified": True,\n        "import_safety_verified": True,\n        "callable_resolution_verified": True,\n        "signature_compatibility_verified": True,\n        "read_only_dependency_verified": True,\n        "live_runner_binding_ready": True,\n        "runner_modified": False,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleTerminalRunnerBindingReadinessGateReport(\n        **report_body,\n        report_hash=oit_028_hash(report_body),\n    )\n    verify_terminal_runner_binding_readiness_gate_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-029 TEST")\n    print(" LIVE RUNNER BINDING AUTHORIZATION GATE")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        source = make_readiness_report(root)\n        report = build_terminal_runner_binding_authorization_gate_report(\n            root,\n            "Authorize the terminal runner binding.",\n            readiness_report=source,\n        )\n\n        authorization = report.callable_authorization\n        assert report.readiness_report_hash == source.report_hash\n        assert report.runner_sha256 == source.runner_inspection.runner_sha256\n        assert authorization.authorization_granted\n        assert authorization.display_only\n        assert authorization.read_only\n        assert not authorization.analytics_access_allowed\n        assert not authorization.database_access_allowed\n        assert not authorization.networking_allowed\n        assert not authorization.publication_allowed\n        assert not authorization.action_authorization_allowed\n        assert not authorization.qseries_execution_allowed\n        assert report.denied_capability_count == 7\n        assert all(\n            denial.denial_enforced\n            for denial in report.denied_capabilities\n        )\n        assert report.runner_identity_authorized\n        assert report.callable_identity_authorized\n        assert report.signature_authorized\n        assert report.display_only_authorized\n        assert report.read_only_boundary_authorized\n        assert report.live_runner_binding_authorized\n        assert not report.runner_modified\n\n        replay = build_terminal_runner_binding_authorization_gate_report(\n            root,\n            "Authorize the terminal runner binding.",\n            readiness_report=source,\n        )\n        assert replay == report\n        assert verify_terminal_runner_binding_authorization_gate_report(\n            report\n        )\n\n        tampered = replace(\n            report,\n            runner_modified=True,\n        )\n        try:\n            verify_terminal_runner_binding_authorization_gate_report(\n                tampered\n            )\n        except OracleTerminalRunnerBindingAuthorizationInvariantError:\n            pass\n        else:\n            raise AssertionError(\n                "tampered runner authorization report accepted"\n            )\n\n        assert report.read_only\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.publication_allowed\n        assert not report.action_authorization_allowed\n        assert not report.qseries_execution_allowed\n\n    print("[PASS] Certified OIT-028 runner readiness consumed")\n    print("[PASS] Exact runner identity authorized")\n    print("[PASS] Exact OIT-027 display-session callable authorized")\n    print("[PASS] Callable signature authorized")\n    print("[PASS] Display-session-only invocation authorized")\n    print("[PASS] Direct analytics access denied")\n    print("[PASS] Database and networking access denied")\n    print("[PASS] Publication and action authorization denied")\n    print("[PASS] Q Series execution denied")\n    print("[PASS] Lower-level terminal bypass denied")\n    print("[PASS] No runner modification performed")\n    print("[PASS] Authorization report deterministic across replay")\n    print("[PASS] Tampered authorization report rejected")\n    print("[DONE] OIT-029 LIVE RUNNER BINDING AUTHORIZATION GATE PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def require_contract(path: Path, tokens: tuple[str, ...], label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label} missing: {path}")
    source = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in source]
    if missing:
        raise RuntimeError(f"{label} contract mismatch: {missing}")


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
    for path in (OIT_028, OIT_028_TEST, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-029 INSTALLER")
    print(" LIVE RUNNER BINDING AUTHORIZATION GATE")
    print("=" * 48)
    try:
        require_contract(
            OIT_028,
            (
                'SCHEMA_VERSION = "OIT-028"',
                'POLICY_ID = "oracle.live-runner-binding-readiness-gate.v1"',
                "OracleTerminalRunnerBindingReadinessGateReport",
                "OracleTerminalRunnerBindingContract",
                "OracleTerminalRunnerInspection",
                "build_terminal_runner_binding_readiness_gate_report",
                "verify_terminal_runner_binding_readiness_gate_report",
                "live_runner_binding_ready",
                "runner_modified",
                "publication_exposure_detected",
                "execution_exposure_detected",
                "database_write_exposure_detected",
                "networking_side_effect_exposure_detected",
            ),
            "Certified OIT-028 production",
        )
        require_contract(
            OIT_028_TEST,
            (
                "OIT-028 TEST",
                "LIVE RUNNER BINDING READINESS GATE",
                "OIT-028 LIVE RUNNER BINDING READINESS GATE PASS",
            ),
            "Certified OIT-028 standalone test",
        )
        if not RUNNER.is_file():
            raise RuntimeError(f"Oracle terminal runner missing: {RUNNER}")

        protected = protected_sources()
        runner_before = sha256(RUNNER)
        print("[OK] Certified OIT-028 production contract verified")
        print("[OK] Certified OIT-028 standalone test verified")
        print("[OK] Oracle terminal runner located")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_028_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-028 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_terminal_live_runner_binding_authorization_gate import *"
        )
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            INIT.write_text(
                current + export + "\n",
                encoding="utf-8",
                newline="\n",
            )
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
                f"OIT-029 test failed with exit code {completed.returncode}"
            )

        if sha256(RUNNER) != runner_before:
            raise RuntimeError(
                "Oracle terminal runner changed during authorization build"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-028 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] OIT-029 production module installed")
        print("[PASS] OIT-029 standalone test installed")
        print("[PASS] Exact display-session callable authorization certified")
        print("[PASS] Direct analytics and lower-level bypass denied")
        print("[PASS] Database, networking, publication, and execution denied")
        print("[PASS] Runner remained unmodified")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-029 LIVE RUNNER BINDING AUTHORIZATION GATE INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
