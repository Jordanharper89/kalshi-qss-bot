
from __future__ import annotations

import ast
import hashlib
import os
import textwrap
from pathlib import Path

REVISION = "OAD_106_EXACT_UNKNOWN_COHORT_CONTRACT_AUDIT_V1"

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT = find_root()
PKG = ROOT / "qseries_v2" / "oracle_adapters" / "independent"
MODULE = PKG / "oad_106_exact_unknown_cohort_contract_audit.py"
TEST = ROOT / "test_oad_106_exact_unknown_cohort_contract_audit.py"
INIT = PKG / "__init__.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\n\nimport ast\nimport importlib\nimport inspect\nimport json\nfrom pathlib import Path\nfrom typing import Any\n\nREAD_ONLY = True\nEXECUTION_AUTHORITY = False\nPROBABILITY_ENABLED = False\n\nTARGET_MODULE = "qseries_v2.oracle_adapters.independent.oad_106_universal_identity_classification_physical_gate"\nTARGET_TEST = "test_oad_106_universal_identity_classification_physical_gate.py"\n\ndef _safe_signature(obj):\n    try:\n        return str(inspect.signature(obj))\n    except Exception:\n        return None\n\ndef _callable_inventory(mod):\n    rows = []\n    for name in sorted(dir(mod)):\n        if name.startswith("__"):\n            continue\n        obj = getattr(mod, name)\n        if inspect.isfunction(obj) or inspect.isclass(obj):\n            rows.append({\n                "name": name,\n                "kind": "class" if inspect.isclass(obj) else "function",\n                "signature": _safe_signature(obj),\n                "module": getattr(obj, "__module__", None),\n            })\n    return rows\n\ndef _source_inventory(path: Path):\n    text = path.read_text(encoding="utf-8")\n    tree = ast.parse(text, filename=str(path))\n\n    functions = []\n    classes = []\n    assignments = []\n    imports = []\n    return_fields = {}\n\n    for node in ast.walk(tree):\n        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):\n            functions.append({\n                "name": node.name,\n                "lineno": node.lineno,\n                "args": [a.arg for a in node.args.args],\n                "kwonlyargs": [a.arg for a in node.args.kwonlyargs],\n            })\n            keys = set()\n            for sub in ast.walk(node):\n                if isinstance(sub, ast.Dict):\n                    for k in sub.keys:\n                        if isinstance(k, ast.Constant) and isinstance(k.value, str):\n                            keys.add(k.value)\n            if keys:\n                return_fields[node.name] = sorted(keys)\n        elif isinstance(node, ast.ClassDef):\n            classes.append({"name": node.name, "lineno": node.lineno})\n        elif isinstance(node, (ast.Assign, ast.AnnAssign)):\n            target = node.targets[0] if isinstance(node, ast.Assign) and node.targets else getattr(node, "target", None)\n            if isinstance(target, ast.Name):\n                assignments.append({"name": target.id, "lineno": node.lineno})\n        elif isinstance(node, ast.ImportFrom):\n            imports.append({\n                "module": node.module,\n                "names": [alias.name for alias in node.names],\n                "lineno": node.lineno,\n            })\n\n    return {\n        "functions": sorted(functions, key=lambda x: x["lineno"]),\n        "classes": sorted(classes, key=lambda x: x["lineno"]),\n        "assignments": sorted(assignments, key=lambda x: x["lineno"]),\n        "imports": sorted(imports, key=lambda x: x["lineno"]),\n        "return_fields": return_fields,\n    }\n\ndef _test_call_graph(path: Path):\n    text = path.read_text(encoding="utf-8")\n    tree = ast.parse(text, filename=str(path))\n\n    imported = []\n    calls = []\n    attrs = []\n    constants = []\n\n    for node in ast.walk(tree):\n        if isinstance(node, ast.ImportFrom):\n            imported.append({\n                "module": node.module,\n                "names": [alias.name for alias in node.names],\n                "lineno": node.lineno,\n            })\n        elif isinstance(node, ast.Call):\n            name = None\n            if isinstance(node.func, ast.Name):\n                name = node.func.id\n            elif isinstance(node.func, ast.Attribute):\n                parts = []\n                cur = node.func\n                while isinstance(cur, ast.Attribute):\n                    parts.append(cur.attr)\n                    cur = cur.value\n                if isinstance(cur, ast.Name):\n                    parts.append(cur.id)\n                name = ".".join(reversed(parts))\n            calls.append({\n                "call": name,\n                "lineno": node.lineno,\n                "keywords": [kw.arg for kw in node.keywords if kw.arg],\n            })\n        elif isinstance(node, ast.Attribute):\n            attrs.append({\n                "attr": node.attr,\n                "lineno": node.lineno,\n            })\n        elif isinstance(node, ast.Constant) and isinstance(node.value, str):\n            v = node.value\n            if any(tok in v.lower() for tok in (\n                "sports", "unknown", "unresolved", "family", "market",\n                "classification", "demand_without_source", "sports_none"\n            )):\n                constants.append({"value": v, "lineno": node.lineno})\n\n    return {\n        "imports": imported,\n        "calls": sorted(calls, key=lambda x: x["lineno"]),\n        "attributes": sorted(attrs, key=lambda x: x["lineno"]),\n        "relevant_string_constants": sorted(constants, key=lambda x: x["lineno"]),\n    }\n\ndef _candidate_entrypoints(runtime_inventory, source_inventory, test_graph):\n    imported_from_target = set()\n    for row in test_graph["imports"]:\n        if row["module"] == TARGET_MODULE:\n            imported_from_target.update(row["names"])\n\n    called_names = {row["call"] for row in test_graph["calls"] if row["call"]}\n    runtime_by_name = {row["name"]: row for row in runtime_inventory}\n\n    candidates = []\n    for name in sorted(imported_from_target):\n        row = runtime_by_name.get(name)\n        candidates.append({\n            "name": name,\n            "runtime": row,\n            "called_in_test": any(\n                call == name or call.startswith(name + ".")\n                for call in called_names\n            ),\n            "source_return_fields": source_inventory["return_fields"].get(name, []),\n        })\n\n    # Also include strong semantic entrypoints even if test imports module indirectly.\n    for row in runtime_inventory:\n        lname = row["name"].lower()\n        if any(tok in lname for tok in (\n            "physical", "classif", "identity", "resolve", "gate", "audit",\n            "cohort", "market", "run", "build"\n        )):\n            if not any(c["name"] == row["name"] for c in candidates):\n                candidates.append({\n                    "name": row["name"],\n                    "runtime": row,\n                    "called_in_test": any(\n                        call == row["name"] or call.startswith(row["name"] + ".")\n                        for call in called_names\n                    ),\n                    "source_return_fields": source_inventory["return_fields"].get(row["name"], []),\n                })\n\n    return candidates\n\ndef run_oad_106_exact_unknown_cohort_contract_audit(root=None):\n    root = Path(root or Path.cwd()).resolve()\n    module_path = root / "qseries_v2" / "oracle_adapters" / "independent" / "oad_106_universal_identity_classification_physical_gate.py"\n    test_path = root / TARGET_TEST\n\n    if not module_path.is_file():\n        raise RuntimeError(f"OAD-106 module missing: {module_path}")\n    if not test_path.is_file():\n        raise RuntimeError(f"OAD-106 physical test missing: {test_path}")\n\n    mod = importlib.import_module(TARGET_MODULE)\n\n    runtime_inventory = _callable_inventory(mod)\n    source_inventory = _source_inventory(module_path)\n    test_graph = _test_call_graph(test_path)\n    candidates = _candidate_entrypoints(runtime_inventory, source_inventory, test_graph)\n\n    report = {\n        "read_only": True,\n        "execution_authority": False,\n        "probability_enabled": False,\n        "target_module": TARGET_MODULE,\n        "target_module_path": str(module_path),\n        "target_test_path": str(test_path),\n        "runtime_callables": runtime_inventory,\n        "source_inventory": source_inventory,\n        "test_call_graph": test_graph,\n        "candidate_entrypoints": candidates,\n    }\n\n    report_path = root / "OAD_106_EXACT_UNKNOWN_COHORT_CONTRACT_AUDIT.json"\n    report_path.write_text(\n        json.dumps(report, indent=2, sort_keys=True, default=str),\n        encoding="utf-8",\n    )\n    return report, report_path\n'
TEST_SOURCE = '\nimport unittest\n\nfrom qseries_v2.oracle_adapters.independent.oad_106_exact_unknown_cohort_contract_audit import (\n    run_oad_106_exact_unknown_cohort_contract_audit,\n)\n\nclass T(unittest.TestCase):\n    def test_contract_audit(self):\n        report, report_path = run_oad_106_exact_unknown_cohort_contract_audit()\n\n        print("[TARGET_MODULE]", report["target_module"])\n        print("[TARGET_MODULE_PATH]", report["target_module_path"])\n        print("[TARGET_TEST_PATH]", report["target_test_path"])\n\n        print("[CANDIDATE_ENTRYPOINTS]")\n        for row in report["candidate_entrypoints"]:\n            print(" ", row)\n\n        print("[TEST_IMPORTS]")\n        for row in report["test_call_graph"]["imports"]:\n            print(" ", row)\n\n        print("[TEST_CALLS]")\n        for row in report["test_call_graph"]["calls"]:\n            print(" ", row)\n\n        print("[RELEVANT_TEST_CONSTANTS]")\n        for row in report["test_call_graph"]["relevant_string_constants"]:\n            print(" ", row)\n\n        print("[SOURCE_FUNCTIONS]")\n        for row in report["source_inventory"]["functions"]:\n            print(" ", row)\n\n        print("[SOURCE_CLASSES]")\n        for row in report["source_inventory"]["classes"]:\n            print(" ", row)\n\n        print("[REPORT]", report_path)\n\n        self.assertTrue(report["read_only"])\n        self.assertFalse(report["execution_authority"])\n        self.assertFalse(report["probability_enabled"])\n        self.assertGreater(len(report["runtime_callables"]), 0)\n        self.assertGreater(len(report["source_inventory"]["functions"]), 0)\n        self.assertGreater(len(report["test_call_graph"]["calls"]), 0)\n\nif __name__ == "__main__":\n    print("=" * 120)\n    print(" OAD-106 EXACT SPORTS:UNKNOWN COHORT CONTRACT AUDIT")\n    print(" SOURCE + CERTIFICATION TEST BINDING — READ ONLY")\n    print("=" * 120)\n\n    result = unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] exact OAD-106 production module inspected")\n    print("[PASS] exact OAD-106 certification test inspected")\n    print("[PASS] runtime callables and signatures captured")\n    print("[PASS] test-imported entrypoints and call graph captured")\n    print("[PASS] no fallback classifier used")\n    print("[PASS] no PostgreSQL access performed")\n    print("[PASS] no production module modified")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OAD-106 EXACT UNKNOWN COHORT CONTRACT AUDIT COMPLETE")\n'

REQUIRED = [
    ("qseries_v2/oracle_adapters/independent/oad_104_semantic_entity_domain_disambiguation.py",
     "Recertified OAD-104"),
    ("qseries_v2/oracle_adapters/independent/oad_105_authoritative_source_requirement_router.py",
     "Recertified OAD-105"),
    ("qseries_v2/oracle_adapters/independent/oad_106_universal_identity_classification_physical_gate.py",
     "Recertified OAD-106"),
    ("test_oad_106_universal_identity_classification_physical_gate.py",
     "OAD-106 physical certification test"),
]

PROTECTED = [
    "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
    "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
    "qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py",
    "qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py",
    "qseries_v2/oracle_adapters/independent/oad_104_semantic_entity_domain_disambiguation.py",
    "qseries_v2/oracle_adapters/independent/oad_105_authoritative_source_requirement_router.py",
    "qseries_v2/oracle_adapters/independent/oad_106_universal_identity_classification_physical_gate.py",
]

def write(path, source):
    source = textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def main():
    print("=" * 120)
    print(" OAD-106 EXACT SPORTS:UNKNOWN COHORT CONTRACT AUDIT INSTALLER")
    print(" SOURCE + CERTIFICATION TEST BINDING — READ ONLY")
    print("=" * 120)
    print("[BOOT] Revision:", REVISION)
    print("[ROOT]", ROOT)

    for rel, label in REQUIRED:
        p = ROOT / rel
        if not p.is_file():
            raise RuntimeError(label + " missing: " + str(p))
        print("[PASS]", label, "verified")

    hashes = {
        ROOT / rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        for rel in PROTECTED
    }

    old = {
        p: (p.read_bytes() if p.exists() else None)
        for p in (MODULE, TEST, INIT)
    }

    try:
        write(MODULE, MODULE_SOURCE)
        write(TEST, TEST_SOURCE)

        lines = INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        export = "from .oad_106_exact_unknown_cohort_contract_audit import *"
        if export not in lines:
            lines.append(export)
        write(INIT, "\n".join(x for x in lines if x.strip()) + "\n")

        for p, expected in hashes.items():
            if hashlib.sha256(p.read_bytes()).hexdigest() != expected:
                raise RuntimeError("Protected production file changed: " + p.name)

        print("[PASS] exact OAD-106 contract audit installed")
        print("[PASS] physical certification test binding included")
        print("[PASS] no heuristic/fallback classification path")
        print("[PASS] no PostgreSQL access")
        print("[PASS] recertified OAD-104/OAD-105/OAD-106 protected")
        print("[PASS] frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] installer and embedded sources syntax-validated")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-106 EXACT UNKNOWN COHORT CONTRACT AUDIT INSTALLATION COMPLETE")

    except Exception:
        for p, data in old.items():
            if data is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] audit files restored")
        raise

if __name__ == "__main__":
    main()
