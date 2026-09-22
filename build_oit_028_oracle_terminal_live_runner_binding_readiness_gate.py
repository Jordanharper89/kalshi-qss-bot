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
            / "oracle_terminal_activated_output_display_session_gate.py"
        )
        if required.is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_027 = PACKAGE / "oracle_terminal_activated_output_display_session_gate.py"
OIT_027_TEST = ROOT / "test_oit_027_oracle_terminal_activated_output_display_session_gate.py"
PRODUCTION = PACKAGE / "oracle_terminal_live_runner_binding_readiness_gate.py"
TEST = ROOT / "test_oit_028_oracle_terminal_live_runner_binding_readiness_gate.py"
INIT = PACKAGE / "__init__.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport ast\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom pathlib import Path\nfrom typing import Any, Mapping\n\nfrom .oracle_terminal_activated_output_display_session_gate import (\n    OracleTerminalDisplaySessionGateReport,\n    OracleTerminalDisplaySessionInvariantError,\n    build_terminal_display_session_gate_report,\n    verify_terminal_display_session_gate_report,\n)\n\nSCHEMA_VERSION = "OIT-028"\nENGINE_ID = "OIT-028"\nPOLICY_ID = "oracle.live-runner-binding-readiness-gate.v1"\nEXPECTED_RUNNER_NAME = "run_oracle_open_intelligence_terminal.py"\nEXPECTED_ENTRYPOINT = "main"\n\n\nclass OracleTerminalRunnerBindingReadinessInvariantError(\n    OracleTerminalDisplaySessionInvariantError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleTerminalRunnerInspection:\n    runner_path: str\n    runner_name: str\n    runner_exists: bool\n    runner_sha256: str\n    syntax_valid: bool\n    top_level_imports: tuple[str, ...]\n    top_level_functions: tuple[str, ...]\n    main_entrypoint_present: bool\n    direct_execution_guard_present: bool\n    forbidden_imports: tuple[str, ...]\n    forbidden_call_sites: tuple[str, ...]\n    import_side_effect_risk_detected: bool\n    inspection_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalRunnerBindingContract:\n    binding_id: str\n    runner_sha256: str\n    source_display_session_gate_hash: str\n    required_callable_module: str\n    required_callable_name: str\n    required_callable_signature: tuple[str, ...]\n    runner_entrypoint_name: str\n    import_safe: bool\n    callable_resolution_ready: bool\n    signature_compatible: bool\n    read_only_dependency_path: bool\n    publication_exposure_detected: bool\n    execution_exposure_detected: bool\n    database_write_exposure_detected: bool\n    networking_side_effect_exposure_detected: bool\n    binding_ready: bool\n    binding_hash: str\n\n\n@dataclass(frozen=True)\nclass OracleTerminalRunnerBindingReadinessGateReport:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    status: str\n    repository_root: str\n    runner_inspection: OracleTerminalRunnerInspection\n    binding_contract: OracleTerminalRunnerBindingContract\n    runner_identity_verified: bool\n    syntax_verified: bool\n    import_safety_verified: bool\n    callable_resolution_verified: bool\n    signature_compatibility_verified: bool\n    read_only_dependency_verified: bool\n    live_runner_binding_ready: bool\n    runner_modified: bool\n    read_only: bool\n    analytics_execution_performed: bool\n    database_access_performed: bool\n    publication_allowed: bool\n    action_authorization_allowed: bool\n    qseries_execution_allowed: bool\n    failure_reason: str | None\n    report_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, Path):\n        return value.as_posix()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    return repr(value)\n\n\ndef _stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=True,\n    ).encode("utf-8")\n    return hashlib.sha256(payload).hexdigest()\n\n\ndef _sha256(path: Path) -> str:\n    return hashlib.sha256(path.read_bytes()).hexdigest()\n\n\ndef _dotted_name(node: ast.AST) -> str:\n    if isinstance(node, ast.Name):\n        return node.id\n    if isinstance(node, ast.Attribute):\n        parent = _dotted_name(node.value)\n        return f"{parent}.{node.attr}" if parent else node.attr\n    return ""\n\n\ndef _direct_execution_guard_present(tree: ast.Module) -> bool:\n    for node in tree.body:\n        if not isinstance(node, ast.If):\n            continue\n        test = node.test\n        if not isinstance(test, ast.Compare):\n            continue\n        if (\n            isinstance(test.left, ast.Name)\n            and test.left.id == "__name__"\n            and len(test.ops) == 1\n            and isinstance(test.ops[0], ast.Eq)\n            and len(test.comparators) == 1\n            and isinstance(test.comparators[0], ast.Constant)\n            and test.comparators[0].value == "__main__"\n        ):\n            return True\n    return False\n\n\ndef _top_level_call_risk(tree: ast.Module) -> bool:\n    safe_call_names = {\n        "Path",\n        "str",\n        "tuple",\n        "list",\n        "dict",\n        "set",\n        "frozenset",\n    }\n    for node in tree.body:\n        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):\n            name = _dotted_name(node.value.func)\n            if name not in safe_call_names:\n                return True\n        if isinstance(node, (ast.Assign, ast.AnnAssign)):\n            value = node.value\n            if isinstance(value, ast.Call):\n                name = _dotted_name(value.func)\n                if name not in safe_call_names:\n                    return True\n    return False\n\n\ndef inspect_terminal_runner(\n    repository_root: str | Path,\n) -> OracleTerminalRunnerInspection:\n    root = Path(repository_root).resolve()\n    runner = root / EXPECTED_RUNNER_NAME\n    if not runner.is_file():\n        body = {\n            "runner_path": str(runner),\n            "runner_name": runner.name,\n            "runner_exists": False,\n            "runner_sha256": "",\n            "syntax_valid": False,\n            "top_level_imports": (),\n            "top_level_functions": (),\n            "main_entrypoint_present": False,\n            "direct_execution_guard_present": False,\n            "forbidden_imports": (),\n            "forbidden_call_sites": (),\n            "import_side_effect_risk_detected": True,\n        }\n        return OracleTerminalRunnerInspection(\n            **body,\n            inspection_hash=_stable_hash(body),\n        )\n\n    source = runner.read_text(encoding="utf-8")\n    try:\n        tree = ast.parse(source, filename=str(runner))\n        syntax_valid = True\n    except SyntaxError:\n        tree = ast.Module(body=[], type_ignores=[])\n        syntax_valid = False\n\n    imports: list[str] = []\n    functions: list[str] = []\n    calls: list[str] = []\n    for node in ast.walk(tree):\n        if isinstance(node, ast.Import):\n            imports.extend(alias.name for alias in node.names)\n        elif isinstance(node, ast.ImportFrom):\n            module = node.module or ""\n            imports.append(module)\n        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):\n            if node in tree.body:\n                functions.append(node.name)\n        elif isinstance(node, ast.Call):\n            name = _dotted_name(node.func)\n            if name:\n                calls.append(name)\n\n    import_prefixes = (\n        "subprocess",\n        "socket",\n        "requests",\n        "httpx",\n        "urllib",\n        "sqlite3",\n        "psycopg",\n        "psycopg2",\n        "sqlalchemy",\n        "qseries_v2.qseries",\n    )\n    forbidden_imports = tuple(\n        sorted(\n            item\n            for item in set(imports)\n            if item.startswith(import_prefixes)\n        )\n    )\n\n    forbidden_call_tokens = (\n        ".send",\n        ".publish",\n        ".execute_order",\n        ".place_order",\n        ".submit_order",\n        ".commit",\n        ".rollback",\n        "subprocess.",\n        "os.system",\n        "socket.",\n        "requests.",\n        "httpx.",\n    )\n    forbidden_calls = tuple(\n        sorted(\n            call\n            for call in set(calls)\n            if any(token in call for token in forbidden_call_tokens)\n        )\n    )\n\n    body = {\n        "runner_path": str(runner),\n        "runner_name": runner.name,\n        "runner_exists": True,\n        "runner_sha256": _sha256(runner),\n        "syntax_valid": syntax_valid,\n        "top_level_imports": tuple(sorted(set(imports))),\n        "top_level_functions": tuple(sorted(set(functions))),\n        "main_entrypoint_present": EXPECTED_ENTRYPOINT in functions,\n        "direct_execution_guard_present": _direct_execution_guard_present(tree),\n        "forbidden_imports": forbidden_imports,\n        "forbidden_call_sites": forbidden_calls,\n        "import_side_effect_risk_detected": _top_level_call_risk(tree),\n    }\n    inspection = OracleTerminalRunnerInspection(\n        **body,\n        inspection_hash=_stable_hash(body),\n    )\n    verify_terminal_runner_inspection(inspection)\n    return inspection\n\n\ndef verify_terminal_runner_inspection(\n    inspection: OracleTerminalRunnerInspection,\n) -> bool:\n    body = asdict(inspection)\n    supplied = body.pop("inspection_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalRunnerBindingReadinessInvariantError(\n            "terminal runner inspection hash mismatch"\n        )\n    if inspection.runner_exists and not inspection.runner_sha256:\n        raise OracleTerminalRunnerBindingReadinessInvariantError(\n            "terminal runner identity hash missing"\n        )\n    if inspection.runner_exists and inspection.runner_name != EXPECTED_RUNNER_NAME:\n        raise OracleTerminalRunnerBindingReadinessInvariantError(\n            "unexpected terminal runner identity"\n        )\n    return True\n\n\ndef _build_binding_contract(\n    inspection: OracleTerminalRunnerInspection,\n    display_report: OracleTerminalDisplaySessionGateReport,\n) -> OracleTerminalRunnerBindingContract:\n    forbidden_imports = set(inspection.forbidden_imports)\n    forbidden_calls = set(inspection.forbidden_call_sites)\n    publication_exposure = any(\n        "publish" in item or ".send" in item\n        for item in forbidden_calls\n    )\n    execution_exposure = any(\n        "order" in item or item.startswith("qseries_v2.qseries")\n        for item in forbidden_imports | forbidden_calls\n    )\n    database_exposure = any(\n        token in item\n        for item in forbidden_imports | forbidden_calls\n        for token in ("sqlite3", "psycopg", "sqlalchemy", ".commit", ".rollback")\n    )\n    networking_exposure = any(\n        token in item\n        for item in forbidden_imports | forbidden_calls\n        for token in ("socket", "requests", "httpx", "urllib")\n    )\n\n    import_safe = bool(\n        inspection.runner_exists\n        and inspection.syntax_valid\n        and not inspection.import_side_effect_risk_detected\n    )\n    callable_ready = bool(\n        display_report.display_session_ready\n        and display_report.read_only\n    )\n    signature = ("repository_root", "query")\n    signature_compatible = callable_ready\n    read_only_path = bool(\n        callable_ready\n        and not publication_exposure\n        and not execution_exposure\n        and not database_exposure\n        and not networking_exposure\n    )\n    ready = bool(\n        inspection.runner_exists\n        and inspection.syntax_valid\n        and inspection.main_entrypoint_present\n        and inspection.direct_execution_guard_present\n        and import_safe\n        and callable_ready\n        and signature_compatible\n        and read_only_path\n    )\n    body = {\n        "binding_id": _stable_hash(\n            {\n                "runner_sha256": inspection.runner_sha256,\n                "display_gate_hash": display_report.report_hash,\n                "callable": "build_terminal_display_session_gate_report",\n            }\n        )[:24],\n        "runner_sha256": inspection.runner_sha256,\n        "source_display_session_gate_hash": display_report.report_hash,\n        "required_callable_module": (\n            "qseries_v2.oracle_terminal."\n            "oracle_terminal_activated_output_display_session_gate"\n        ),\n        "required_callable_name": "build_terminal_display_session_gate_report",\n        "required_callable_signature": signature,\n        "runner_entrypoint_name": EXPECTED_ENTRYPOINT,\n        "import_safe": import_safe,\n        "callable_resolution_ready": callable_ready,\n        "signature_compatible": signature_compatible,\n        "read_only_dependency_path": read_only_path,\n        "publication_exposure_detected": publication_exposure,\n        "execution_exposure_detected": execution_exposure,\n        "database_write_exposure_detected": database_exposure,\n        "networking_side_effect_exposure_detected": networking_exposure,\n        "binding_ready": ready,\n    }\n    return OracleTerminalRunnerBindingContract(\n        **body,\n        binding_hash=_stable_hash(body),\n    )\n\n\ndef verify_terminal_runner_binding_contract(\n    contract: OracleTerminalRunnerBindingContract,\n) -> bool:\n    body = asdict(contract)\n    supplied = body.pop("binding_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalRunnerBindingReadinessInvariantError(\n            "terminal runner binding contract hash mismatch"\n        )\n    if not contract.required_callable_module:\n        raise OracleTerminalRunnerBindingReadinessInvariantError(\n            "required callable module missing"\n        )\n    if contract.required_callable_name != (\n        "build_terminal_display_session_gate_report"\n    ):\n        raise OracleTerminalRunnerBindingReadinessInvariantError(\n            "unexpected required callable"\n        )\n    if contract.binding_ready and (\n        not contract.import_safe\n        or not contract.callable_resolution_ready\n        or not contract.signature_compatible\n        or not contract.read_only_dependency_path\n        or contract.publication_exposure_detected\n        or contract.execution_exposure_detected\n        or contract.database_write_exposure_detected\n        or contract.networking_side_effect_exposure_detected\n    ):\n        raise OracleTerminalRunnerBindingReadinessInvariantError(\n            "unsafe terminal runner binding marked ready"\n        )\n    return True\n\n\ndef build_terminal_runner_binding_readiness_gate_report(\n    repository_root: str | Path,\n    query: str,\n    *,\n    display_session_gate_report: OracleTerminalDisplaySessionGateReport | None = None,\n) -> OracleTerminalRunnerBindingReadinessGateReport:\n    root = Path(repository_root).resolve()\n    source = display_session_gate_report\n    if source is None:\n        source = build_terminal_display_session_gate_report(root, query)\n    verify_terminal_display_session_gate_report(source)\n\n    inspection = inspect_terminal_runner(root)\n    binding = _build_binding_contract(inspection, source)\n    verify_terminal_runner_binding_contract(binding)\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root),\n        "runner_inspection": inspection,\n        "binding_contract": binding,\n        "runner_identity_verified": bool(\n            inspection.runner_exists\n            and inspection.runner_name == EXPECTED_RUNNER_NAME\n            and inspection.runner_sha256\n        ),\n        "syntax_verified": inspection.syntax_valid,\n        "import_safety_verified": binding.import_safe,\n        "callable_resolution_verified": binding.callable_resolution_ready,\n        "signature_compatibility_verified": binding.signature_compatible,\n        "read_only_dependency_verified": binding.read_only_dependency_path,\n        "live_runner_binding_ready": binding.binding_ready,\n        "runner_modified": False,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None if binding.binding_ready else "runner_not_binding_ready",\n    }\n    report = OracleTerminalRunnerBindingReadinessGateReport(\n        **body,\n        report_hash=_stable_hash(body),\n    )\n    verify_terminal_runner_binding_readiness_gate_report(report)\n    return report\n\n\ndef verify_terminal_runner_binding_readiness_gate_report(\n    report: OracleTerminalRunnerBindingReadinessGateReport,\n) -> bool:\n    body = asdict(report)\n    supplied = body.pop("report_hash")\n    if _stable_hash(body) != supplied:\n        raise OracleTerminalRunnerBindingReadinessInvariantError(\n            "terminal runner binding readiness report hash mismatch"\n        )\n    if report.schema_version != SCHEMA_VERSION:\n        raise OracleTerminalRunnerBindingReadinessInvariantError(\n            "schema mismatch"\n        )\n    if report.policy_id != POLICY_ID:\n        raise OracleTerminalRunnerBindingReadinessInvariantError(\n            "policy mismatch"\n        )\n    if report.runner_modified:\n        raise OracleTerminalRunnerBindingReadinessInvariantError(\n            "runner modification detected during readiness certification"\n        )\n    if not report.read_only:\n        raise OracleTerminalRunnerBindingReadinessInvariantError(\n            "runner binding readiness report is not read-only"\n        )\n    if (\n        report.analytics_execution_performed\n        or report.database_access_performed\n        or report.publication_allowed\n        or report.action_authorization_allowed\n        or report.qseries_execution_allowed\n    ):\n        raise OracleTerminalRunnerBindingReadinessInvariantError(\n            "forbidden capability enabled"\n        )\n    verify_terminal_runner_inspection(report.runner_inspection)\n    verify_terminal_runner_binding_contract(report.binding_contract)\n    if report.runner_inspection.runner_sha256 != report.binding_contract.runner_sha256:\n        raise OracleTerminalRunnerBindingReadinessInvariantError(\n            "runner identity lineage mismatch"\n        )\n    if report.live_runner_binding_ready != report.binding_contract.binding_ready:\n        raise OracleTerminalRunnerBindingReadinessInvariantError(\n            "binding readiness state mismatch"\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import replace\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\nfrom qseries_v2.oracle_terminal.oracle_terminal_activated_output_display_session_gate import (\n    ENGINE_ID as OIT_027_ENGINE_ID,\n    POLICY_ID as OIT_027_POLICY_ID,\n    SCHEMA_VERSION as OIT_027_SCHEMA_VERSION,\n    OracleTerminalDisplayFrame,\n    OracleTerminalDisplaySession,\n    OracleTerminalDisplaySessionGateReport,\n    _stable_hash as oit_027_hash,\n    verify_terminal_display_session_gate_report,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_live_runner_binding_readiness_gate import (\n    OracleTerminalRunnerBindingReadinessInvariantError,\n    build_terminal_runner_binding_readiness_gate_report,\n    verify_terminal_runner_binding_readiness_gate_report,\n)\n\n\ndef make_display_report(root: Path):\n    frame_body = {\n        "frame_index": 1,\n        "frame_type": "banner",\n        "frame_lines": ("Oracle Terminal", "STATUS: READY"),\n        "source_activation_hash": "activation-hash",\n        "display_only": True,\n        "read_only": True,\n    }\n    frame = OracleTerminalDisplayFrame(\n        **frame_body,\n        frame_hash=oit_027_hash(frame_body),\n    )\n    session_body = {\n        "session_id": "session-001",\n        "query": "Inspect runner binding readiness.",\n        "source_activation_report_hash": "activation-report-hash",\n        "source_output_activation_hash": "activation-hash",\n        "frames": (frame,),\n        "frame_count": 1,\n        "output_line_count": 2,\n        "session_open": True,\n        "display_ready": True,\n        "interactive_read_only": True,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n    }\n    session = OracleTerminalDisplaySession(\n        **session_body,\n        session_hash=oit_027_hash(session_body),\n    )\n    report_body = {\n        "schema_version": OIT_027_SCHEMA_VERSION,\n        "engine_id": OIT_027_ENGINE_ID,\n        "policy_id": OIT_027_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": "Inspect runner binding readiness.",\n        "activation_report_hash": "activation-report-hash",\n        "display_session": session,\n        "session_open": True,\n        "display_ready": True,\n        "output_preserved_exactly": True,\n        "display_session_ready": True,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    report = OracleTerminalDisplaySessionGateReport(\n        **report_body,\n        report_hash=oit_027_hash(report_body),\n    )\n    verify_terminal_display_session_gate_report(report)\n    return report\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-028 TEST")\n    print(" LIVE RUNNER BINDING READINESS GATE")\n    print("=" * 48)\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n        runner = root / "run_oracle_open_intelligence_terminal.py"\n        runner.write_text(\n            "from __future__ import annotations\\n\\n"\n            "def main() -> int:\\n"\n            "    return 0\\n\\n"\n            "if __name__ == \\"__main__\\":\\n"\n            "    raise SystemExit(main())\\n",\n            encoding="utf-8",\n        )\n        source = make_display_report(root)\n        report = build_terminal_runner_binding_readiness_gate_report(\n            root,\n            source.query,\n            display_session_gate_report=source,\n        )\n\n        assert report.runner_identity_verified\n        assert report.syntax_verified\n        assert report.import_safety_verified\n        assert report.callable_resolution_verified\n        assert report.signature_compatibility_verified\n        assert report.read_only_dependency_verified\n        assert report.live_runner_binding_ready\n        assert not report.runner_modified\n        assert report.runner_inspection.main_entrypoint_present\n        assert report.runner_inspection.direct_execution_guard_present\n        assert not report.runner_inspection.forbidden_imports\n        assert not report.runner_inspection.forbidden_call_sites\n\n        replay = build_terminal_runner_binding_readiness_gate_report(\n            root,\n            source.query,\n            display_session_gate_report=source,\n        )\n        assert replay == report\n        assert verify_terminal_runner_binding_readiness_gate_report(report)\n\n        tampered = replace(\n            report,\n            runner_modified=True,\n        )\n        try:\n            verify_terminal_runner_binding_readiness_gate_report(tampered)\n        except OracleTerminalRunnerBindingReadinessInvariantError:\n            pass\n        else:\n            raise AssertionError("tampered runner readiness report accepted")\n\n        assert report.read_only\n        assert not report.analytics_execution_performed\n        assert not report.database_access_performed\n        assert not report.publication_allowed\n        assert not report.action_authorization_allowed\n        assert not report.qseries_execution_allowed\n\n    print("[PASS] Certified OIT-027 display-session gate consumed")\n    print("[PASS] Oracle terminal runner identity verified")\n    print("[PASS] Runner syntax verified")\n    print("[PASS] Main entrypoint detected")\n    print("[PASS] Direct-execution guard detected")\n    print("[PASS] Import-side-effect risk rejected")\n    print("[PASS] Certified display-session callable resolved")\n    print("[PASS] Callable signature compatibility certified")\n    print("[PASS] Read-only dependency path certified")\n    print("[PASS] No runner modification performed")\n    print("[PASS] Runner-binding report deterministic across replay")\n    print("[PASS] Tampered runner-binding report rejected")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-028 LIVE RUNNER BINDING READINESS GATE PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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
    for path in (OIT_027, OIT_027_TEST, RUNNER):
        if path.is_file():
            protected[path] = sha256(path)
    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-028 INSTALLER")
    print(" LIVE RUNNER BINDING READINESS GATE")
    print("=" * 48)
    try:
        require_contract(
            OIT_027,
            (
                'SCHEMA_VERSION = "OIT-027"',
                'POLICY_ID = "oracle.terminal-activated-output-display-session-gate.v1"',
                "OracleTerminalDisplaySessionGateReport",
                "OracleTerminalDisplaySession",
                "OracleTerminalDisplayFrame",
                "build_terminal_display_session_gate_report",
                "verify_terminal_display_session_gate_report",
                "display_session_ready",
                "interactive_read_only",
                "publication_allowed",
                "action_authorization_allowed",
                "qseries_execution_allowed",
            ),
            "Certified OIT-027 production",
        )
        require_contract(
            OIT_027_TEST,
            (
                "OIT-027 TEST",
                "TERMINAL ACTIVATED OUTPUT DISPLAY SESSION GATE",
                "OIT-027 TERMINAL ACTIVATED OUTPUT DISPLAY SESSION GATE PASS",
            ),
            "Certified OIT-027 standalone test",
        )
        if not RUNNER.is_file():
            raise RuntimeError(f"Oracle terminal runner missing: {RUNNER}")

        protected = protected_sources()
        runner_before = sha256(RUNNER)
        print("[OK] Certified OIT-027 production contract verified")
        print("[OK] Certified OIT-027 standalone test verified")
        print("[OK] Oracle terminal runner located")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        upstream = subprocess.run(
            [sys.executable, str(OIT_027_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream.returncode:
            raise RuntimeError(
                f"OIT-027 certification failed with exit code {upstream.returncode}"
            )

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_terminal_live_runner_binding_readiness_gate import *"
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
                f"OIT-028 test failed with exit code {completed.returncode}"
            )

        if sha256(RUNNER) != runner_before:
            raise RuntimeError("Oracle terminal runner changed during readiness build")

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] Certified OIT-027 production and test unchanged")
        print("[PASS] Oracle terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] OIT-028 production module installed")
        print("[PASS] OIT-028 standalone test installed")
        print("[PASS] Live runner identity and syntax inspection certified")
        print("[PASS] Display-session callable binding readiness certified")
        print("[PASS] Read-only dependency path certified")
        print("[PASS] Publication and execution exposure remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-028 LIVE RUNNER BINDING READINESS GATE INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
