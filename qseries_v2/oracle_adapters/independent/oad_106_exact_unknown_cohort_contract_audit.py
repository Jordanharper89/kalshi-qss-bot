from __future__ import annotations

import ast
import importlib
import inspect
import json
from pathlib import Path
from typing import Any

READ_ONLY = True
EXECUTION_AUTHORITY = False
PROBABILITY_ENABLED = False

TARGET_MODULE = "qseries_v2.oracle_adapters.independent.oad_106_universal_identity_classification_physical_gate"
TARGET_TEST = "test_oad_106_universal_identity_classification_physical_gate.py"

def _safe_signature(obj):
    try:
        return str(inspect.signature(obj))
    except Exception:
        return None

def _callable_inventory(mod):
    rows = []
    for name in sorted(dir(mod)):
        if name.startswith("__"):
            continue
        obj = getattr(mod, name)
        if inspect.isfunction(obj) or inspect.isclass(obj):
            rows.append({
                "name": name,
                "kind": "class" if inspect.isclass(obj) else "function",
                "signature": _safe_signature(obj),
                "module": getattr(obj, "__module__", None),
            })
    return rows

def _source_inventory(path: Path):
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))

    functions = []
    classes = []
    assignments = []
    imports = []
    return_fields = {}

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({
                "name": node.name,
                "lineno": node.lineno,
                "args": [a.arg for a in node.args.args],
                "kwonlyargs": [a.arg for a in node.args.kwonlyargs],
            })
            keys = set()
            for sub in ast.walk(node):
                if isinstance(sub, ast.Dict):
                    for k in sub.keys:
                        if isinstance(k, ast.Constant) and isinstance(k.value, str):
                            keys.add(k.value)
            if keys:
                return_fields[node.name] = sorted(keys)
        elif isinstance(node, ast.ClassDef):
            classes.append({"name": node.name, "lineno": node.lineno})
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) and node.targets else getattr(node, "target", None)
            if isinstance(target, ast.Name):
                assignments.append({"name": target.id, "lineno": node.lineno})
        elif isinstance(node, ast.ImportFrom):
            imports.append({
                "module": node.module,
                "names": [alias.name for alias in node.names],
                "lineno": node.lineno,
            })

    return {
        "functions": sorted(functions, key=lambda x: x["lineno"]),
        "classes": sorted(classes, key=lambda x: x["lineno"]),
        "assignments": sorted(assignments, key=lambda x: x["lineno"]),
        "imports": sorted(imports, key=lambda x: x["lineno"]),
        "return_fields": return_fields,
    }

def _test_call_graph(path: Path):
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))

    imported = []
    calls = []
    attrs = []
    constants = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.append({
                "module": node.module,
                "names": [alias.name for alias in node.names],
                "lineno": node.lineno,
            })
        elif isinstance(node, ast.Call):
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                parts = []
                cur = node.func
                while isinstance(cur, ast.Attribute):
                    parts.append(cur.attr)
                    cur = cur.value
                if isinstance(cur, ast.Name):
                    parts.append(cur.id)
                name = ".".join(reversed(parts))
            calls.append({
                "call": name,
                "lineno": node.lineno,
                "keywords": [kw.arg for kw in node.keywords if kw.arg],
            })
        elif isinstance(node, ast.Attribute):
            attrs.append({
                "attr": node.attr,
                "lineno": node.lineno,
            })
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value
            if any(tok in v.lower() for tok in (
                "sports", "unknown", "unresolved", "family", "market",
                "classification", "demand_without_source", "sports_none"
            )):
                constants.append({"value": v, "lineno": node.lineno})

    return {
        "imports": imported,
        "calls": sorted(calls, key=lambda x: x["lineno"]),
        "attributes": sorted(attrs, key=lambda x: x["lineno"]),
        "relevant_string_constants": sorted(constants, key=lambda x: x["lineno"]),
    }

def _candidate_entrypoints(runtime_inventory, source_inventory, test_graph):
    imported_from_target = set()
    for row in test_graph["imports"]:
        if row["module"] == TARGET_MODULE:
            imported_from_target.update(row["names"])

    called_names = {row["call"] for row in test_graph["calls"] if row["call"]}
    runtime_by_name = {row["name"]: row for row in runtime_inventory}

    candidates = []
    for name in sorted(imported_from_target):
        row = runtime_by_name.get(name)
        candidates.append({
            "name": name,
            "runtime": row,
            "called_in_test": any(
                call == name or call.startswith(name + ".")
                for call in called_names
            ),
            "source_return_fields": source_inventory["return_fields"].get(name, []),
        })

    # Also include strong semantic entrypoints even if test imports module indirectly.
    for row in runtime_inventory:
        lname = row["name"].lower()
        if any(tok in lname for tok in (
            "physical", "classif", "identity", "resolve", "gate", "audit",
            "cohort", "market", "run", "build"
        )):
            if not any(c["name"] == row["name"] for c in candidates):
                candidates.append({
                    "name": row["name"],
                    "runtime": row,
                    "called_in_test": any(
                        call == row["name"] or call.startswith(row["name"] + ".")
                        for call in called_names
                    ),
                    "source_return_fields": source_inventory["return_fields"].get(row["name"], []),
                })

    return candidates

def run_oad_106_exact_unknown_cohort_contract_audit(root=None):
    root = Path(root or Path.cwd()).resolve()
    module_path = root / "qseries_v2" / "oracle_adapters" / "independent" / "oad_106_universal_identity_classification_physical_gate.py"
    test_path = root / TARGET_TEST

    if not module_path.is_file():
        raise RuntimeError(f"OAD-106 module missing: {module_path}")
    if not test_path.is_file():
        raise RuntimeError(f"OAD-106 physical test missing: {test_path}")

    mod = importlib.import_module(TARGET_MODULE)

    runtime_inventory = _callable_inventory(mod)
    source_inventory = _source_inventory(module_path)
    test_graph = _test_call_graph(test_path)
    candidates = _candidate_entrypoints(runtime_inventory, source_inventory, test_graph)

    report = {
        "read_only": True,
        "execution_authority": False,
        "probability_enabled": False,
        "target_module": TARGET_MODULE,
        "target_module_path": str(module_path),
        "target_test_path": str(test_path),
        "runtime_callables": runtime_inventory,
        "source_inventory": source_inventory,
        "test_call_graph": test_graph,
        "candidate_entrypoints": candidates,
    }

    report_path = root / "OAD_106_EXACT_UNKNOWN_COHORT_CONTRACT_AUDIT.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return report, report_path
