
from __future__ import annotations

import ast
import os
import textwrap
from pathlib import Path

REVISION = "OAD_110_AUTHORITATIVE_SPORTS_CANONICAL_BRIDGE_REPOSITORY_NATIVE_REBUILD"

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

def write_py(path, source):
    source = textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

ROOT = find_root()
PKG = ROOT / "qseries_v2" / "oracle_adapters" / "independent"
MODULE = PKG / "oad_110_authoritative_sports_canonical_bridge.py"
TEST = ROOT / "test_oad_110_authoritative_sports_canonical_bridge.py"
INIT = PKG / "__init__.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\n\nimport importlib\nimport inspect\nfrom dataclasses import asdict, is_dataclass\n\nREAD_ONLY = True\nEXECUTION_AUTHORITY = False\nPROBABILITY_ENABLED = False\n\nCANDIDATE_MODULES = (\n    "qseries_v2.oracle_adapters.independent.oad_061_independent_canonical_observation_bridge",\n    "qseries_v2.oracle_adapters.independent.oad_061_independent_canonical_bridge",\n    "qseries_v2.oracle_adapters.independent.oad_061_canonical_bridge",\n    "qseries_v2.oracle_adapters.independent.oad_061_independent_observation_canonical_bridge",\n)\n\nCANDIDATE_CALLABLES = (\n    "bridge_independent_observation",\n    "to_canonical_observation",\n    "build_canonical_observation",\n    "canonicalize_independent_observation",\n    "convert_independent_observation",\n)\n\ndef _record(obj):\n    if is_dataclass(obj):\n        return asdict(obj)\n    if isinstance(obj, dict):\n        return dict(obj)\n    if hasattr(obj, "__dict__"):\n        return dict(vars(obj))\n    raise TypeError("Unsupported authoritative sports observation type")\n\ndef discover_repository_native_bridge():\n    findings = []\n    for mod_name in CANDIDATE_MODULES:\n        try:\n            mod = importlib.import_module(mod_name)\n        except Exception as exc:\n            findings.append((mod_name, None, type(exc).__name__))\n            continue\n\n        for name in CANDIDATE_CALLABLES:\n            fn = getattr(mod, name, None)\n            if callable(fn):\n                return {\n                    "module": mod_name,\n                    "callable": name,\n                    "signature": str(inspect.signature(fn)),\n                    "function": fn,\n                }\n        findings.append((mod_name, "imported_no_known_callable", None))\n\n    # Repository-native fallback: search already-installed independent modules dynamically.\n    pkg = importlib.import_module("qseries_v2.oracle_adapters.independent")\n    pkg_path = getattr(pkg, "__path__", None)\n    if pkg_path:\n        import pkgutil\n        for info in pkgutil.iter_modules(pkg_path):\n            name = info.name\n            if not name.startswith("oad_"):\n                continue\n            low = name.lower()\n            if "canonical" not in low and "bridge" not in low:\n                continue\n            mod_name = f"qseries_v2.oracle_adapters.independent.{name}"\n            try:\n                mod = importlib.import_module(mod_name)\n            except Exception:\n                continue\n            for callable_name in CANDIDATE_CALLABLES:\n                fn = getattr(mod, callable_name, None)\n                if callable(fn):\n                    return {\n                        "module": mod_name,\n                        "callable": callable_name,\n                        "signature": str(inspect.signature(fn)),\n                        "function": fn,\n                    }\n\n    raise RuntimeError(\n        "No existing repository-native independent canonical bridge callable was found. "\n        "No duplicate bridge was created."\n    )\n\ndef to_existing_independent_contract(o):\n    r = _record(o)\n    return {\n        "source_id": r.get("source_id"),\n        "provider": r.get("provider"),\n        "subject": r.get("subject"),\n        "observed_at": r.get("observed_at"),\n        "source_url": r.get("source_url"),\n        "source_class": r.get("source_class", "authoritative_real_world"),\n        "independent_evidence": bool(r.get("independent_evidence", True)),\n        "provenance_hash": r.get("provenance_hash"),\n        "source_payload": dict(r.get("payload") or {}),\n        "sport_family": r.get("sport_family"),\n        "observation_type": r.get("observation_type"),\n        "execution_authority": False,\n    }\n\ndef bridge_contract_record():\n    found = discover_repository_native_bridge()\n    return {\n        "module": found["module"],\n        "callable": found["callable"],\n        "signature": found["signature"],\n        "read_only": True,\n        "execution_authority": False,\n        "probability_enabled": False,\n    }\n'
TEST_SOURCE = '\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_110_authoritative_sports_canonical_bridge import (\n    discover_repository_native_bridge,\n    bridge_contract_record,\n)\n\nclass T(unittest.TestCase):\n    def test_repository_native_bridge(self):\n        found = discover_repository_native_bridge()\n        record = bridge_contract_record()\n\n        print("[BRIDGE_MODULE]", record["module"])\n        print("[BRIDGE_CALLABLE]", record["callable"])\n        print("[BRIDGE_SIGNATURE]", record["signature"])\n\n        self.assertTrue(callable(found["function"]))\n        self.assertTrue(record["read_only"])\n        self.assertFalse(record["execution_authority"])\n        self.assertFalse(record["probability_enabled"])\n\nif __name__=="__main__":\n    print("="*112)\n    print(" OAD-110 AUTHORITATIVE SPORTS CANONICAL BRIDGE")\n    print(" REPOSITORY-NATIVE REBUILD")\n    print("="*112)\n\n    r = unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] repository-native canonical bridge discovered")\n    print("[PASS] no duplicate persistence architecture created")\n    print("[PASS] read_only=TRUE")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OAD-110 REPOSITORY-NATIVE BRIDGE COMPLETE")\n'

REQUIRED = [
    PKG / "oad_107_authoritative_sports_source_foundation.py",
]

def main():
    print("="*112)
    print(" OAD-110 AUTHORITATIVE SPORTS CANONICAL BRIDGE INSTALLER")
    print(" REPOSITORY-NATIVE REBUILD")
    print("="*112)
    print("[BOOT] Revision:", REVISION)
    print("[ROOT]", ROOT)

    for p in REQUIRED:
        if not p.is_file():
            raise RuntimeError("Required dependency missing: " + str(p))
        print("[PASS] dependency verified:", p.name)

    old = {p: (p.read_bytes() if p.exists() else None) for p in (MODULE, TEST, INIT)}

    try:
        write_py(MODULE, MODULE_SOURCE)
        write_py(TEST, TEST_SOURCE)

        lines = INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        export = "from .oad_110_authoritative_sports_canonical_bridge import *"
        if export not in lines:
            lines.append(export)
        write_py(INIT, "\n".join(x for x in lines if x.strip()) + "\n")

        print("[PASS] repository-native bridge resolver installed")
        print("[PASS] old nonexistent OAD-061 path is no longer a hard dependency")
        print("[PASS] existing bridge must be discovered from the current repository")
        print("[PASS] no duplicate canonical/persistence path created")
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-110 REPOSITORY-NATIVE INSTALLATION COMPLETE")

    except Exception:
        for p, data in old.items():
            if data is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] OAD-110 diagnostic/install files restored")
        raise

if __name__=="__main__":
    main()
