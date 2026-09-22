from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .oracle_live_intelligence_runtime_discovery_and_binding import (
    OracleLiveIntelligenceBindingInvariantError,
    discover_live_intelligence_binding,
    verify_live_intelligence_binding,
)

SCHEMA_VERSION = "OIT-003"
ENGINE_ID = "OIT-003"
POLICY_ID = "oracle.live-intelligence-activation-discovery.v1"
DISCOVERY_STATUS = "live_intelligence_activation_discovery_ready"

ANALYTICS_PACKAGE = "qseries_v2/oracle_intelligence/analytics"
LIVE_ACQUISITION_ROOTS = (
    "qseries_v2/oracle_intelligence/live_acquisition",
    "qseries_v2/oracle_intelligence/live_acquisition_model",
)
INTELLIGENCE_RUNTIME_ROOT = "runtime/oracle_intelligence"

ENTRY_NAME_TOKENS = (
    "activate", "run", "execute", "process", "evaluate", "analyze",
    "build", "materialize", "persist", "dispatch", "invoke",
)
ENTRY_FILE_TOKENS = (
    "activation", "pipeline", "runtime", "execution", "invocation",
    "worker", "dispatch", "analytics", "evaluation",
)
PERSISTENCE_CALL_TOKENS = (
    "write_text", "write_bytes", "open", "dump", "dumps",
    "persist", "save", "append", "commit",
)
INPUT_PARAMETER_EXCLUSIONS = {
    "self", "cls", "args", "kwargs", "repository_root", "root",
    "runtime_root", "output_root", "output_path", "path",
}
_RUNTIME_LITERAL = re.compile(
    r"runtime[\\/]+oracle_intelligence(?:[\\/]+[A-Za-z0-9_.-]+)*",
    re.IGNORECASE,
)


class OracleLiveIntelligenceActivationDiscoveryInvariantError(
    OracleLiveIntelligenceBindingInvariantError
):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported canonical type: {type(value)!r}")


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _module_name(relative_path: str) -> str:
    path = relative_path[:-3] if relative_path.endswith(".py") else relative_path
    return path.replace("/", ".").replace("\\", ".")


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _iter_python_files(root: Path) -> Iterable[Path]:
    if not root.is_dir():
        return ()
    return (
        path for path in sorted(root.rglob("*.py"))
        if "__pycache__" not in path.parts
    )


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _runtime_targets(text: str) -> tuple[str, ...]:
    return tuple(sorted({
        match.replace("\\", "/").rstrip("/")
        for match in _RUNTIME_LITERAL.findall(text)
    }))


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts = [func.attr]
        value = func.value
        while isinstance(value, ast.Attribute):
            parts.append(value.attr)
            value = value.value
        if isinstance(value, ast.Name):
            parts.append(value.id)
        return ".".join(reversed(parts))
    return ""


def _annotation_text(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


def _signature_inputs(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str, ...]:
    ordered = [
        *node.args.posonlyargs,
        *node.args.args,
        *node.args.kwonlyargs,
    ]
    result = []
    for arg in ordered:
        if arg.arg in INPUT_PARAMETER_EXCLUSIONS:
            continue
        annotation = _annotation_text(arg.annotation)
        result.append(f"{arg.arg}: {annotation}" if annotation else arg.arg)
    return tuple(result)


def _imports_from_tree(tree: ast.AST, current_module: str) -> tuple[str, ...]:
    imported: set[str] = set()
    package_parts = current_module.split(".")[:-1]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package_parts[: max(0, len(package_parts) - node.level + 1)]
                if node.module:
                    base.extend(node.module.split("."))
                if base:
                    imported.add(".".join(base))
            elif node.module:
                imported.add(node.module)
    return tuple(sorted(imported))


def _local_module_path(repository_root: Path, module_name: str) -> Path | None:
    base = repository_root / Path(*module_name.split("."))
    module_file = base.with_suffix(".py")
    package_file = base / "__init__.py"
    if module_file.is_file():
        return module_file
    if package_file.is_file():
        return package_file
    return None


@dataclass(frozen=True)
class OracleAnalyticsEntryCandidate:
    module: str
    relative_path: str
    callable_name: str
    callable_kind: str
    required_inputs: tuple[str, ...]
    imported_modules: tuple[str, ...]
    persistence_targets: tuple[str, ...]
    score: int
    score_reasons: tuple[str, ...]
    candidate_hash: str


@dataclass(frozen=True)
class OracleActivationDependencyNode:
    module: str
    relative_path: str
    role: str
    syntax_valid: bool
    local_dependencies_present: bool
    dependency_hash: str


@dataclass(frozen=True)
class OracleLiveIntelligenceActivationDiscoveryReceipt:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    analytics_package_present: bool
    analytics_python_file_count: int
    entry_candidates: tuple[OracleAnalyticsEntryCandidate, ...]
    canonical_entry_module: str | None
    canonical_entry_callable: str | None
    required_inputs: tuple[str, ...]
    dependency_chain: tuple[OracleActivationDependencyNode, ...]
    live_acquisition_dependency_present: bool
    persistence_targets: tuple[str, ...]
    canonical_persistence_target: str | None
    static_chain_executable: bool
    activation_readiness: str
    readiness_reasons: tuple[str, ...]
    live_execution_status: str
    existing_intelligence_artifact_count: int
    discovery_only: bool
    analytics_execution_performed: bool
    runtime_artifact_created: bool
    database_access_performed: bool
    module_import_execution_performed: bool
    read_only: bool
    execution_allowed: bool
    publication_allowed: bool
    qseries_mutation_allowed: bool
    receipt_hash: str


def _candidate(
    *,
    repository_root: Path,
    module_path: Path,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    tree: ast.AST,
    source_text: str,
    class_name: str | None = None,
) -> OracleAnalyticsEntryCandidate:
    relative_path = _relative(module_path, repository_root)
    module = _module_name(relative_path)
    callable_name = f"{class_name}.{node.name}" if class_name else node.name
    callable_kind = "method" if class_name else "function"
    imports = _imports_from_tree(tree, module)
    targets = _runtime_targets(source_text)
    calls = {_call_name(item).lower() for item in ast.walk(node) if isinstance(item, ast.Call)}

    score = 0
    reasons: list[str] = []
    lowered_name = node.name.lower()
    lowered_file = module_path.stem.lower()

    matched_name = [token for token in ENTRY_NAME_TOKENS if token in lowered_name]
    if matched_name:
        score += 35
        reasons.append("entry-like callable name")
    matched_file = [token for token in ENTRY_FILE_TOKENS if token in lowered_file]
    if matched_file:
        score += 15
        reasons.append("pipeline/runtime module name")
    if targets:
        score += 30
        reasons.append("declares oracle_intelligence persistence target")
    if any(any(token in call for token in PERSISTENCE_CALL_TOKENS) for call in calls):
        score += 10
        reasons.append("contains persistence-oriented call")
    if any(
        imported.startswith("qseries_v2.oracle_intelligence.live_acquisition")
        for imported in imports
    ):
        score += 25
        reasons.append("imports live acquisition dependency")
    if node.name.startswith("_"):
        score -= 20
        reasons.append("private callable penalty")
    if class_name and class_name.startswith("_"):
        score -= 10
        reasons.append("private owner penalty")
    required_inputs = _signature_inputs(node)
    if required_inputs:
        score += min(10, len(required_inputs) * 2)
        reasons.append("explicit input contract")

    body = {
        "module": module,
        "relative_path": relative_path,
        "callable_name": callable_name,
        "callable_kind": callable_kind,
        "required_inputs": required_inputs,
        "imported_modules": imports,
        "persistence_targets": targets,
        "score": score,
        "score_reasons": tuple(reasons),
    }
    return OracleAnalyticsEntryCandidate(
        **body, candidate_hash=_stable_hash(body)
    )


def _discover_candidates(
    repository_root: Path,
) -> tuple[OracleAnalyticsEntryCandidate, ...]:
    analytics_root = repository_root / ANALYTICS_PACKAGE
    candidates: list[OracleAnalyticsEntryCandidate] = []
    for module_path in _iter_python_files(analytics_root):
        source_text = _safe_read(module_path)
        if not source_text:
            continue
        try:
            tree = ast.parse(source_text, filename=str(module_path))
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                candidate = _candidate(
                    repository_root=repository_root,
                    module_path=module_path,
                    node=node,
                    tree=tree,
                    source_text=source_text,
                )
                if candidate.score > 0:
                    candidates.append(candidate)
            elif isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        candidate = _candidate(
                            repository_root=repository_root,
                            module_path=module_path,
                            node=child,
                            tree=tree,
                            source_text=source_text,
                            class_name=node.name,
                        )
                        if candidate.score > 0:
                            candidates.append(candidate)
    return tuple(sorted(
        candidates,
        key=lambda item: (-item.score, item.relative_path, item.callable_name),
    ))


def _dependency_chain(
    repository_root: Path,
    entry: OracleAnalyticsEntryCandidate | None,
    *,
    maximum_nodes: int = 128,
) -> tuple[OracleActivationDependencyNode, ...]:
    if entry is None:
        return ()
    pending = [entry.module]
    visited: set[str] = set()
    nodes: list[OracleActivationDependencyNode] = []

    while pending and len(nodes) < maximum_nodes:
        module = pending.pop(0)
        if module in visited:
            continue
        visited.add(module)
        path = _local_module_path(repository_root, module)
        if path is None:
            continue
        relative_path = _relative(path, repository_root)
        text = _safe_read(path)
        syntax_valid = False
        imports: tuple[str, ...] = ()
        try:
            tree = ast.parse(text, filename=str(path))
            syntax_valid = True
            imports = _imports_from_tree(tree, module)
        except SyntaxError:
            tree = None

        local_imports = tuple(
            item for item in imports
            if item.startswith("qseries_v2.oracle_intelligence")
        )
        dependencies_present = all(
            _local_module_path(repository_root, item) is not None
            for item in local_imports
        )
        if module.startswith("qseries_v2.oracle_intelligence.live_acquisition"):
            role = "live_acquisition_input"
        elif module == entry.module:
            role = "canonical_analytics_entry"
        elif module.startswith("qseries_v2.oracle_intelligence.analytics"):
            role = "analytics_dependency"
        else:
            role = "oracle_intelligence_dependency"

        body = {
            "module": module,
            "relative_path": relative_path,
            "role": role,
            "syntax_valid": syntax_valid,
            "local_dependencies_present": dependencies_present,
        }
        nodes.append(OracleActivationDependencyNode(
            **body, dependency_hash=_stable_hash(body)
        ))
        for imported in local_imports:
            if imported not in visited and _local_module_path(repository_root, imported):
                pending.append(imported)

    return tuple(nodes)


def discover_live_intelligence_activation(
    *,
    repository_root: Path,
) -> OracleLiveIntelligenceActivationDiscoveryReceipt:
    root = repository_root.resolve()
    analytics_root = root / ANALYTICS_PACKAGE
    analytics_files = tuple(_iter_python_files(analytics_root))
    candidates = _discover_candidates(root)
    entry = candidates[0] if candidates else None
    chain = _dependency_chain(root, entry)

    binding = discover_live_intelligence_binding(repository_root=root)
    verify_live_intelligence_binding(binding)

    all_targets = set(binding.declared_runtime_targets)
    for candidate in candidates:
        all_targets.update(candidate.persistence_targets)
    intelligence_targets = tuple(sorted(
        target for target in all_targets
        if target == INTELLIGENCE_RUNTIME_ROOT
        or target.startswith(INTELLIGENCE_RUNTIME_ROOT + "/")
    ))
    canonical_target = (
        entry.persistence_targets[0]
        if entry and entry.persistence_targets
        else (intelligence_targets[0] if intelligence_targets else None)
    )

    live_dependency = any(
        node.role == "live_acquisition_input" for node in chain
    )
    syntax_ok = bool(chain) and all(node.syntax_valid for node in chain)
    dependencies_ok = bool(chain) and all(
        node.local_dependencies_present for node in chain
    )
    callable_identified = entry is not None
    persistence_identified = canonical_target is not None
    static_executable = bool(
        callable_identified and syntax_ok and dependencies_ok and persistence_identified
    )

    reasons: list[str] = []
    if not analytics_root.is_dir():
        reasons.append("analytics package not found")
    if not callable_identified:
        reasons.append("canonical analytics entry point not identified")
    if callable_identified and not syntax_ok:
        reasons.append("one or more dependency modules fail syntax validation")
    if callable_identified and not dependencies_ok:
        reasons.append("one or more local Oracle dependencies are missing")
    if not live_dependency:
        reasons.append(
            "no direct live-acquisition import found in the minimum static graph; "
            "input may be supplied through a persisted contract or adapter boundary"
        )
    if not persistence_identified:
        reasons.append("canonical runtime/oracle_intelligence target not identified")
    if static_executable:
        reasons.append(
            "static callable, dependency, and persistence checks passed without execution"
        )

    if not callable_identified or not persistence_identified:
        readiness = "not_ready"
    elif not syntax_ok or not dependencies_ok:
        readiness = "blocked"
    elif live_dependency:
        readiness = "ready_for_bounded_activation"
    else:
        readiness = "conditionally_ready_input_boundary_unresolved"

    if binding.binding_active:
        live_status = "persisted_intelligence_output_present"
    elif binding.live_shadow_runtime_present:
        live_status = "live_acquisition_available_analytics_not_persisting"
    else:
        live_status = "analytics_not_running_no_live_acquisition_runtime"

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": DISCOVERY_STATUS,
        "repository_root": root.as_posix(),
        "analytics_package_present": analytics_root.is_dir(),
        "analytics_python_file_count": len(analytics_files),
        "entry_candidates": candidates[:25],
        "canonical_entry_module": entry.module if entry else None,
        "canonical_entry_callable": entry.callable_name if entry else None,
        "required_inputs": entry.required_inputs if entry else (),
        "dependency_chain": chain,
        "live_acquisition_dependency_present": live_dependency,
        "persistence_targets": intelligence_targets,
        "canonical_persistence_target": canonical_target,
        "static_chain_executable": static_executable,
        "activation_readiness": readiness,
        "readiness_reasons": tuple(reasons),
        "live_execution_status": live_status,
        "existing_intelligence_artifact_count": binding.bindable_artifact_count,
        "discovery_only": True,
        "analytics_execution_performed": False,
        "runtime_artifact_created": False,
        "database_access_performed": False,
        "module_import_execution_performed": False,
        "read_only": True,
        "execution_allowed": False,
        "publication_allowed": False,
        "qseries_mutation_allowed": False,
    }
    return OracleLiveIntelligenceActivationDiscoveryReceipt(
        **body, receipt_hash=_stable_hash(body)
    )


def verify_activation_discovery(
    receipt: OracleLiveIntelligenceActivationDiscoveryReceipt,
) -> bool:
    body = asdict(receipt)
    supplied = body.pop("receipt_hash")
    for candidate in receipt.entry_candidates:
        candidate_body = asdict(candidate)
        candidate_hash = candidate_body.pop("candidate_hash")
        if _stable_hash(candidate_body) != candidate_hash:
            raise OracleLiveIntelligenceActivationDiscoveryInvariantError(
                "entry candidate hash mismatch"
            )
    for node in receipt.dependency_chain:
        node_body = asdict(node)
        dependency_hash = node_body.pop("dependency_hash")
        if _stable_hash(node_body) != dependency_hash:
            raise OracleLiveIntelligenceActivationDiscoveryInvariantError(
                "dependency node hash mismatch"
            )
    if _stable_hash(body) != supplied:
        raise OracleLiveIntelligenceActivationDiscoveryInvariantError(
            "activation discovery receipt hash mismatch"
        )
    if not receipt.discovery_only:
        raise OracleLiveIntelligenceActivationDiscoveryInvariantError(
            "discovery-only boundary disabled"
        )
    if (
        receipt.analytics_execution_performed
        or receipt.runtime_artifact_created
        or receipt.database_access_performed
        or receipt.module_import_execution_performed
    ):
        raise OracleLiveIntelligenceActivationDiscoveryInvariantError(
            "discovery performed a prohibited side effect"
        )
    if not receipt.read_only:
        raise OracleLiveIntelligenceActivationDiscoveryInvariantError(
            "activation discovery is not read-only"
        )
    if (
        receipt.execution_allowed
        or receipt.publication_allowed
        or receipt.qseries_mutation_allowed
    ):
        raise OracleLiveIntelligenceActivationDiscoveryInvariantError(
            "unsafe activation boundary"
        )
    return True


def activation_terminal_lines(
    receipt: OracleLiveIntelligenceActivationDiscoveryReceipt,
) -> tuple[str, ...]:
    verify_activation_discovery(receipt)
    chain = " -> ".join(
        f"{node.role}:{node.module}" for node in receipt.dependency_chain
    ) or "not identified"
    inputs = ", ".join(receipt.required_inputs) or "no explicit parameters discovered"
    target = receipt.canonical_persistence_target or "not identified"
    entry = (
        f"{receipt.canonical_entry_module}:{receipt.canonical_entry_callable}"
        if receipt.canonical_entry_module and receipt.canonical_entry_callable
        else "not identified"
    )
    reasons = "; ".join(receipt.readiness_reasons) or "none"
    return (
        "ORACLE LIVE INTELLIGENCE ACTIVATION DISCOVERY",
        f"analytics_entry_point: {entry}",
        f"required_inputs: {inputs}",
        f"dependency_chain: {chain}",
        f"persistence_target: {target}",
        f"activation_readiness: {receipt.activation_readiness}",
        f"readiness_reasons: {reasons}",
        f"live_execution_status: {receipt.live_execution_status}",
        f"existing_intelligence_artifacts: {receipt.existing_intelligence_artifact_count}",
        "discovery_only: true",
        "analytics_execution_performed: false",
        "runtime_artifact_created: false",
        "database_access_performed: false",
        "read_only: true",
        "OIT-004 bounded activation remains disabled.",
    )


def execute_activation_discovery_command(
    *,
    repository_root: Path,
) -> tuple[str, ...]:
    receipt = discover_live_intelligence_activation(
        repository_root=repository_root
    )
    return activation_terminal_lines(receipt)


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "DISCOVERY_STATUS",
    "OracleLiveIntelligenceActivationDiscoveryInvariantError",
    "OracleAnalyticsEntryCandidate",
    "OracleActivationDependencyNode",
    "OracleLiveIntelligenceActivationDiscoveryReceipt",
    "discover_live_intelligence_activation",
    "verify_activation_discovery",
    "activation_terminal_lines",
    "execute_activation_discovery_command",
]
