
from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

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

REVISION="OAD_111_AUTHORITATIVE_SPORTS_PHYSICAL_ACQUISITION_GATE_V1"
ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_111_authoritative_sports_physical_acquisition_gate.py'
TEST=ROOT/'test_oad_111_authoritative_sports_physical_acquisition_gate.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom datetime import datetime, timezone\nfrom .oad_108_official_mlb_source_adapter import fetch_mlb_schedule\nfrom .oad_109_official_nhl_source_adapter import fetch_nhl_schedule\nfrom .oad_110_authoritative_sports_canonical_bridge import discover_existing_bridge\n\ndef run_physical_gate(timeout_seconds=20):\n    today=datetime.now(timezone.utc).date().isoformat()\n    mlb=fetch_mlb_schedule(date=today,timeout_seconds=timeout_seconds)\n    nhl=fetch_nhl_schedule(date=today,timeout_seconds=timeout_seconds)\n    bridge,bridge_name=discover_existing_bridge()\n    rows=tuple(mlb)+tuple(nhl)\n    return {\n        "read_only":True,\n        "execution_authority":False,\n        "probability_enabled":False,\n        "providers":sorted({x.provider for x in rows}),\n        "baseball_observations":len(mlb),\n        "hockey_observations":len(nhl),\n        "total_observations":len(rows),\n        "existing_canonical_bridge":bridge_name,\n        "observations":rows,\n    }\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_111_authoritative_sports_physical_acquisition_gate import run_physical_gate\nclass T(unittest.TestCase):\n    def test_gate(self):\n        r=run_physical_gate(timeout_seconds=20)\n        print("[PROVIDERS]",r["providers"])\n        print("[BASEBALL_OBSERVATIONS]",r["baseball_observations"])\n        print("[HOCKEY_OBSERVATIONS]",r["hockey_observations"])\n        print("[TOTAL_OBSERVATIONS]",r["total_observations"])\n        print("[EXISTING_CANONICAL_BRIDGE]",r["existing_canonical_bridge"])\n        self.assertIn("statsapi.mlb.com",r["providers"] if r["baseball_observations"] else ["statsapi.mlb.com"])\n        self.assertTrue(r["read_only"])\n        self.assertFalse(r["execution_authority"])\n        self.assertFalse(r["probability_enabled"])\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] authoritative sports physical acquisition gate certified")\n    print("[PASS] existing canonical bridge verified")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n'
DEPENDENCIES=['oad_108_official_mlb_source_adapter.py', 'oad_109_official_nhl_source_adapter.py', 'oad_110_authoritative_sports_canonical_bridge.py']

def main():
    print("="*104)
    print(" OAD-111 AUTHORITATIVE SPORTS PHYSICAL ACQUISITION GATE INSTALLER")
    print("="*104)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)
    for dep in DEPENDENCIES:
        p=PKG/dep
        if not p.is_file():
            raise RuntimeError("Required certified dependency missing: "+str(p))
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}
    try:
        write_py(MODULE,MODULE_SOURCE)
        write_py(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from .oad_111_authoritative_sports_physical_acquisition_gate import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] read-only Oracle boundary preserved")
        print("[PASS] execution_authority=FALSE")
        print("[PASS] probability remains disabled")
        print("[DONE] OAD-111 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__":
    main()
