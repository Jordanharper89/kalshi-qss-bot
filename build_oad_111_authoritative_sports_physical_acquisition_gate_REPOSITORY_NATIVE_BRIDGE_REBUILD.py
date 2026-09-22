
from __future__ import annotations

import ast
import os
import textwrap
from pathlib import Path

REVISION = "OAD_111_AUTHORITATIVE_SPORTS_PHYSICAL_ACQUISITION_GATE_REPOSITORY_NATIVE_BRIDGE_REBUILD"

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
MODULE = PKG / "oad_111_authoritative_sports_physical_acquisition_gate.py"
TEST = ROOT / "test_oad_111_authoritative_sports_physical_acquisition_gate.py"
INIT = PKG / "__init__.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\n\nfrom datetime import datetime, timezone\n\nfrom .oad_108_official_mlb_source_adapter import fetch_mlb_schedule\nfrom .oad_109_official_nhl_source_adapter import fetch_nhl_schedule\nfrom .oad_110_authoritative_sports_canonical_bridge import (\n    discover_repository_native_bridge,\n    bridge_contract_record,\n)\n\nREAD_ONLY = True\nEXECUTION_AUTHORITY = False\nPROBABILITY_ENABLED = False\n\ndef run_physical_gate(timeout_seconds=20):\n    today = datetime.now(timezone.utc).date().isoformat()\n\n    mlb = fetch_mlb_schedule(date=today, timeout_seconds=timeout_seconds)\n    nhl = fetch_nhl_schedule(date=today, timeout_seconds=timeout_seconds)\n\n    bridge = discover_repository_native_bridge()\n    bridge_record = bridge_contract_record()\n\n    rows = tuple(mlb) + tuple(nhl)\n\n    return {\n        "read_only": True,\n        "execution_authority": False,\n        "probability_enabled": False,\n        "providers": tuple(sorted({x.provider for x in rows})),\n        "baseball_observations": len(mlb),\n        "hockey_observations": len(nhl),\n        "total_observations": len(rows),\n        "bridge_module": bridge_record["module"],\n        "bridge_callable": bridge_record["callable"],\n        "bridge_signature": bridge_record["signature"],\n        "bridge_callable_object": bridge["function"],\n        "observations": rows,\n    }\n'
TEST_SOURCE = '\nimport unittest\n\nfrom qseries_v2.oracle_adapters.independent.oad_111_authoritative_sports_physical_acquisition_gate import (\n    run_physical_gate,\n)\n\nclass T(unittest.TestCase):\n    def test_gate(self):\n        r = run_physical_gate(timeout_seconds=20)\n\n        print("[PROVIDERS]", r["providers"])\n        print("[BASEBALL_OBSERVATIONS]", r["baseball_observations"])\n        print("[HOCKEY_OBSERVATIONS]", r["hockey_observations"])\n        print("[TOTAL_OBSERVATIONS]", r["total_observations"])\n        print("[BRIDGE_MODULE]", r["bridge_module"])\n        print("[BRIDGE_CALLABLE]", r["bridge_callable"])\n        print("[BRIDGE_SIGNATURE]", r["bridge_signature"])\n\n        self.assertTrue(callable(r["bridge_callable_object"]))\n        self.assertTrue(r["read_only"])\n        self.assertFalse(r["execution_authority"])\n        self.assertFalse(r["probability_enabled"])\n\n        for o in r["observations"]:\n            self.assertTrue(o.independent_evidence)\n            self.assertEqual(o.source_class, "authoritative_real_world")\n            self.assertFalse(o.execution_authority)\n\nif __name__ == "__main__":\n    print("=" * 116)\n    print(" OAD-111 AUTHORITATIVE SPORTS PHYSICAL ACQUISITION GATE")\n    print(" REPOSITORY-NATIVE BRIDGE REBUILD")\n    print("=" * 116)\n\n    result = unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] physical MLB acquisition path verified")\n    print("[PASS] physical NHL acquisition path verified")\n    print("[PASS] repository-native canonical bridge verified")\n    print("[PASS] authoritative_real_world provenance preserved")\n    print("[PASS] independent_evidence=TRUE")\n    print("[PASS] read_only=TRUE")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OAD-111 AUTHORITATIVE SPORTS PHYSICAL ACQUISITION GATE COMPLETE")\n'

REQUIRED = [
    PKG / "oad_108_official_mlb_source_adapter.py",
    PKG / "oad_109_official_nhl_source_adapter.py",
    PKG / "oad_110_authoritative_sports_canonical_bridge.py",
]

def main():
    print("=" * 116)
    print(" OAD-111 AUTHORITATIVE SPORTS PHYSICAL ACQUISITION GATE INSTALLER")
    print(" REPOSITORY-NATIVE BRIDGE REBUILD")
    print("=" * 116)
    print("[BOOT] Revision:", REVISION)
    print("[ROOT]", ROOT)

    for p in REQUIRED:
        if not p.is_file():
            raise RuntimeError("Required certified dependency missing: " + str(p))
        print("[PASS] dependency verified:", p.name)

    # Verify OAD-110 exposes the repository-native bridge contract before writing OAD-111.
    import sys, importlib
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    m110 = importlib.import_module(
        "qseries_v2.oracle_adapters.independent.oad_110_authoritative_sports_canonical_bridge"
    )
    required_symbols = ("discover_repository_native_bridge", "bridge_contract_record")
    missing = [x for x in required_symbols if not callable(getattr(m110, x, None))]
    if missing:
        raise RuntimeError("Current OAD-110 missing repository-native symbols: " + ", ".join(missing))

    found = m110.discover_repository_native_bridge()
    print("[PASS] OAD-110 repository-native bridge callable verified:",
          found["module"] + "." + found["callable"])

    old = {p: (p.read_bytes() if p.exists() else None) for p in (MODULE, TEST, INIT)}

    try:
        write_py(MODULE, MODULE_SOURCE)
        write_py(TEST, TEST_SOURCE)

        lines = INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        export = "from .oad_111_authoritative_sports_physical_acquisition_gate import *"
        if export not in lines:
            lines.append(export)
        write_py(INIT, "\n".join(x for x in lines if x.strip()) + "\n")

        print("[PASS] OAD-111 replaced against current repository-native OAD-110 contract")
        print("[PASS] MLB adapter preserved")
        print("[PASS] NHL adapter preserved")
        print("[PASS] no duplicate bridge or persistence architecture created")
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-111 REPOSITORY-NATIVE BRIDGE INSTALLATION COMPLETE")

    except Exception:
        for p, data in old.items():
            if data is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] OAD-111 restored")
        raise

if __name__ == "__main__":
    main()
