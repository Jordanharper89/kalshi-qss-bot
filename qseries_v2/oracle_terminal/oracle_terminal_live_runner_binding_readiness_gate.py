from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_terminal_activated_output_display_session_gate import (
    OracleTerminalDisplaySessionGateReport,
    OracleTerminalDisplaySessionInvariantError,
    build_terminal_display_session_gate_report,
    verify_terminal_display_session_gate_report,
)

SCHEMA_VERSION = "OIT-028"
ENGINE_ID = "OIT-028"
POLICY_ID = "oracle.live-runner-binding-readiness-gate.v1"
EXPECTED_RUNNER_NAME = "run_oracle_open_intelligence_terminal.py"
EXPECTED_ENTRYPOINT = "main"


class OracleTerminalRunnerBindingReadinessInvariantError(
    OracleTerminalDisplaySessionInvariantError
):
    pass


@dataclass(frozen=True)
class OracleTerminalRunnerInspection:
    runner_path: str
    runner_name: str
    runner_exists: bool
    runner_sha256: str
    syntax_valid: bool
    top_level_imports: tuple[str, ...]
    top_level_functions: tuple[str, ...]
    main_entrypoint_present: bool
    direct_execution_guard_present: bool
    forbidden_imports: tuple[str, ...]
    forbidden_call_sites: tuple[str, ...]
    import_side_effect_risk_detected: bool
    inspection_hash: str


@dataclass(frozen=True)
class OracleTerminalRunnerBindingContract:
    binding_id: str
    runner_sha256: str
    source_display_session_gate_hash: str
    required_callable_module: str
    required_callable_name: str
    required_callable_signature: tuple[str, ...]
    runner_entrypoint_name: str
    import_safe: bool
    callable_resolution_ready: bool
    signature_compatible: bool
    read_only_dependency_path: bool
    publication_exposure_detected: bool
    execution_exposure_detected: bool
    database_write_exposure_detected: bool
    networking_side_effect_exposure_detected: bool
    binding_ready: bool
    binding_hash: str


@dataclass(frozen=True)
class OracleTerminalRunnerBindingReadinessGateReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    runner_inspection: OracleTerminalRunnerInspection
    binding_contract: OracleTerminalRunnerBindingContract
    runner_identity_verified: bool
    syntax_verified: bool
    import_safety_verified: bool
    callable_resolution_verified: bool
    signature_compatibility_verified: bool
    read_only_dependency_verified: bool
    live_runner_binding_ready: bool
    runner_modified: bool
    read_only: bool
    analytics_execution_performed: bool
    database_access_performed: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    failure_reason: str | None
    report_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _direct_execution_guard_present(tree: ast.Module) -> bool:
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not isinstance(test, ast.Compare):
            continue
        if (
            isinstance(test.left, ast.Name)
            and test.left.id == "__name__"
            and len(test.ops) == 1
            and isinstance(test.ops[0], ast.Eq)
            and len(test.comparators) == 1
            and isinstance(test.comparators[0], ast.Constant)
            and test.comparators[0].value == "__main__"
        ):
            return True
    return False


def _top_level_call_risk(tree: ast.Module) -> bool:
    safe_call_names = {
        "Path",
        "str",
        "tuple",
        "list",
        "dict",
        "set",
        "frozenset",
    }
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            name = _dotted_name(node.value.func)
            if name not in safe_call_names:
                return True
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            if isinstance(value, ast.Call):
                name = _dotted_name(value.func)
                if name not in safe_call_names:
                    return True
    return False


def inspect_terminal_runner(
    repository_root: str | Path,
) -> OracleTerminalRunnerInspection:
    root = Path(repository_root).resolve()
    runner = root / EXPECTED_RUNNER_NAME
    if not runner.is_file():
        body = {
            "runner_path": str(runner),
            "runner_name": runner.name,
            "runner_exists": False,
            "runner_sha256": "",
            "syntax_valid": False,
            "top_level_imports": (),
            "top_level_functions": (),
            "main_entrypoint_present": False,
            "direct_execution_guard_present": False,
            "forbidden_imports": (),
            "forbidden_call_sites": (),
            "import_side_effect_risk_detected": True,
        }
        return OracleTerminalRunnerInspection(
            **body,
            inspection_hash=_stable_hash(body),
        )

    source = runner.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(runner))
        syntax_valid = True
    except SyntaxError:
        tree = ast.Module(body=[], type_ignores=[])
        syntax_valid = False

    imports: list[str] = []
    functions: list[str] = []
    calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append(module)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node in tree.body:
                functions.append(node.name)
        elif isinstance(node, ast.Call):
            name = _dotted_name(node.func)
            if name:
                calls.append(name)

    import_prefixes = (
        "subprocess",
        "socket",
        "requests",
        "httpx",
        "urllib",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "qseries_v2.qseries",
    )
    forbidden_imports = tuple(
        sorted(
            item
            for item in set(imports)
            if item.startswith(import_prefixes)
        )
    )

    forbidden_call_tokens = (
        ".send",
        ".publish",
        ".execute_order",
        ".place_order",
        ".submit_order",
        ".commit",
        ".rollback",
        "subprocess.",
        "os.system",
        "socket.",
        "requests.",
        "httpx.",
    )
    forbidden_calls = tuple(
        sorted(
            call
            for call in set(calls)
            if any(token in call for token in forbidden_call_tokens)
        )
    )

    body = {
        "runner_path": str(runner),
        "runner_name": runner.name,
        "runner_exists": True,
        "runner_sha256": _sha256(runner),
        "syntax_valid": syntax_valid,
        "top_level_imports": tuple(sorted(set(imports))),
        "top_level_functions": tuple(sorted(set(functions))),
        "main_entrypoint_present": EXPECTED_ENTRYPOINT in functions,
        "direct_execution_guard_present": _direct_execution_guard_present(tree),
        "forbidden_imports": forbidden_imports,
        "forbidden_call_sites": forbidden_calls,
        "import_side_effect_risk_detected": _top_level_call_risk(tree),
    }
    inspection = OracleTerminalRunnerInspection(
        **body,
        inspection_hash=_stable_hash(body),
    )
    verify_terminal_runner_inspection(inspection)
    return inspection


def verify_terminal_runner_inspection(
    inspection: OracleTerminalRunnerInspection,
) -> bool:
    body = asdict(inspection)
    supplied = body.pop("inspection_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalRunnerBindingReadinessInvariantError(
            "terminal runner inspection hash mismatch"
        )
    if inspection.runner_exists and not inspection.runner_sha256:
        raise OracleTerminalRunnerBindingReadinessInvariantError(
            "terminal runner identity hash missing"
        )
    if inspection.runner_exists and inspection.runner_name != EXPECTED_RUNNER_NAME:
        raise OracleTerminalRunnerBindingReadinessInvariantError(
            "unexpected terminal runner identity"
        )
    return True


def _build_binding_contract(
    inspection: OracleTerminalRunnerInspection,
    display_report: OracleTerminalDisplaySessionGateReport,
) -> OracleTerminalRunnerBindingContract:
    forbidden_imports = set(inspection.forbidden_imports)
    forbidden_calls = set(inspection.forbidden_call_sites)
    publication_exposure = any(
        "publish" in item or ".send" in item
        for item in forbidden_calls
    )
    execution_exposure = any(
        "order" in item or item.startswith("qseries_v2.qseries")
        for item in forbidden_imports | forbidden_calls
    )
    database_exposure = any(
        token in item
        for item in forbidden_imports | forbidden_calls
        for token in ("sqlite3", "psycopg", "sqlalchemy", ".commit", ".rollback")
    )
    networking_exposure = any(
        token in item
        for item in forbidden_imports | forbidden_calls
        for token in ("socket", "requests", "httpx", "urllib")
    )

    import_safe = bool(
        inspection.runner_exists
        and inspection.syntax_valid
        and not inspection.import_side_effect_risk_detected
    )
    callable_ready = bool(
        display_report.display_session_ready
        and display_report.read_only
    )
    signature = ("repository_root", "query")
    signature_compatible = callable_ready
    read_only_path = bool(
        callable_ready
        and not publication_exposure
        and not execution_exposure
        and not database_exposure
        and not networking_exposure
    )
    ready = bool(
        inspection.runner_exists
        and inspection.syntax_valid
        and inspection.main_entrypoint_present
        and inspection.direct_execution_guard_present
        and import_safe
        and callable_ready
        and signature_compatible
        and read_only_path
    )
    body = {
        "binding_id": _stable_hash(
            {
                "runner_sha256": inspection.runner_sha256,
                "display_gate_hash": display_report.report_hash,
                "callable": "build_terminal_display_session_gate_report",
            }
        )[:24],
        "runner_sha256": inspection.runner_sha256,
        "source_display_session_gate_hash": display_report.report_hash,
        "required_callable_module": (
            "qseries_v2.oracle_terminal."
            "oracle_terminal_activated_output_display_session_gate"
        ),
        "required_callable_name": "build_terminal_display_session_gate_report",
        "required_callable_signature": signature,
        "runner_entrypoint_name": EXPECTED_ENTRYPOINT,
        "import_safe": import_safe,
        "callable_resolution_ready": callable_ready,
        "signature_compatible": signature_compatible,
        "read_only_dependency_path": read_only_path,
        "publication_exposure_detected": publication_exposure,
        "execution_exposure_detected": execution_exposure,
        "database_write_exposure_detected": database_exposure,
        "networking_side_effect_exposure_detected": networking_exposure,
        "binding_ready": ready,
    }
    return OracleTerminalRunnerBindingContract(
        **body,
        binding_hash=_stable_hash(body),
    )


def verify_terminal_runner_binding_contract(
    contract: OracleTerminalRunnerBindingContract,
) -> bool:
    body = asdict(contract)
    supplied = body.pop("binding_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalRunnerBindingReadinessInvariantError(
            "terminal runner binding contract hash mismatch"
        )
    if not contract.required_callable_module:
        raise OracleTerminalRunnerBindingReadinessInvariantError(
            "required callable module missing"
        )
    if contract.required_callable_name != (
        "build_terminal_display_session_gate_report"
    ):
        raise OracleTerminalRunnerBindingReadinessInvariantError(
            "unexpected required callable"
        )
    if contract.binding_ready and (
        not contract.import_safe
        or not contract.callable_resolution_ready
        or not contract.signature_compatible
        or not contract.read_only_dependency_path
        or contract.publication_exposure_detected
        or contract.execution_exposure_detected
        or contract.database_write_exposure_detected
        or contract.networking_side_effect_exposure_detected
    ):
        raise OracleTerminalRunnerBindingReadinessInvariantError(
            "unsafe terminal runner binding marked ready"
        )
    return True


def build_terminal_runner_binding_readiness_gate_report(
    repository_root: str | Path,
    query: str,
    *,
    display_session_gate_report: OracleTerminalDisplaySessionGateReport | None = None,
) -> OracleTerminalRunnerBindingReadinessGateReport:
    root = Path(repository_root).resolve()
    source = display_session_gate_report
    if source is None:
        source = build_terminal_display_session_gate_report(root, query)
    verify_terminal_display_session_gate_report(source)

    inspection = inspect_terminal_runner(root)
    binding = _build_binding_contract(inspection, source)
    verify_terminal_runner_binding_contract(binding)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "runner_inspection": inspection,
        "binding_contract": binding,
        "runner_identity_verified": bool(
            inspection.runner_exists
            and inspection.runner_name == EXPECTED_RUNNER_NAME
            and inspection.runner_sha256
        ),
        "syntax_verified": inspection.syntax_valid,
        "import_safety_verified": binding.import_safe,
        "callable_resolution_verified": binding.callable_resolution_ready,
        "signature_compatibility_verified": binding.signature_compatible,
        "read_only_dependency_verified": binding.read_only_dependency_path,
        "live_runner_binding_ready": binding.binding_ready,
        "runner_modified": False,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None if binding.binding_ready else "runner_not_binding_ready",
    }
    report = OracleTerminalRunnerBindingReadinessGateReport(
        **body,
        report_hash=_stable_hash(body),
    )
    verify_terminal_runner_binding_readiness_gate_report(report)
    return report


def verify_terminal_runner_binding_readiness_gate_report(
    report: OracleTerminalRunnerBindingReadinessGateReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalRunnerBindingReadinessInvariantError(
            "terminal runner binding readiness report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleTerminalRunnerBindingReadinessInvariantError(
            "schema mismatch"
        )
    if report.policy_id != POLICY_ID:
        raise OracleTerminalRunnerBindingReadinessInvariantError(
            "policy mismatch"
        )
    if report.runner_modified:
        raise OracleTerminalRunnerBindingReadinessInvariantError(
            "runner modification detected during readiness certification"
        )
    if not report.read_only:
        raise OracleTerminalRunnerBindingReadinessInvariantError(
            "runner binding readiness report is not read-only"
        )
    if (
        report.analytics_execution_performed
        or report.database_access_performed
        or report.publication_allowed
        or report.action_authorization_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleTerminalRunnerBindingReadinessInvariantError(
            "forbidden capability enabled"
        )
    verify_terminal_runner_inspection(report.runner_inspection)
    verify_terminal_runner_binding_contract(report.binding_contract)
    if report.runner_inspection.runner_sha256 != report.binding_contract.runner_sha256:
        raise OracleTerminalRunnerBindingReadinessInvariantError(
            "runner identity lineage mismatch"
        )
    if report.live_runner_binding_ready != report.binding_contract.binding_ready:
        raise OracleTerminalRunnerBindingReadinessInvariantError(
            "binding readiness state mismatch"
        )
    return True
