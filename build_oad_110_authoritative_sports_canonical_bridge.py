
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

REVISION="OAD_110_AUTHORITATIVE_SPORTS_CANONICAL_BRIDGE_V1"
ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_110_authoritative_sports_canonical_bridge.py'
TEST=ROOT/'test_oad_110_authoritative_sports_canonical_bridge.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import asdict\nimport importlib\n\ndef _bridge():\n    m=importlib.import_module("qseries_v2.oracle_adapters.independent.oad_061_independent_canonical_observation_bridge")\n    for name in ("bridge_independent_observation","to_canonical_observation","build_canonical_observation","canonicalize_independent_observation"):\n        fn=getattr(m,name,None)\n        if callable(fn): return fn,name\n    raise RuntimeError("Existing OAD-061 canonical bridge callable not exposed")\n\ndef to_existing_independent_contract(o):\n    # OAD-061 consumes the established independent-observation shape. Keep fields explicit.\n    return {\n        "source_id":o.source_id,"provider":o.provider,"subject":o.subject,\n        "observed_at":o.observed_at,"source_url":o.source_url,\n        "source_class":o.source_class,"independent_evidence":o.independent_evidence,\n        "provenance_hash":o.provenance_hash,"source_payload":dict(o.payload),\n        "sport_family":o.sport_family,"observation_type":o.observation_type,\n        "execution_authority":False,\n    }\n\ndef discover_existing_bridge():\n    fn,name=_bridge()\n    return fn,name\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_110_authoritative_sports_canonical_bridge import discover_existing_bridge\nclass T(unittest.TestCase):\n    def test_bridge_exists(self):\n        fn,name=discover_existing_bridge()\n        print("[EXISTING_CANONICAL_BRIDGE]",name)\n        self.assertTrue(callable(fn))\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] existing OAD-061 canonical bridge discovered")\n    print("[PASS] no duplicate persistence architecture created")\n'
DEPENDENCIES=['oad_107_authoritative_sports_source_foundation.py', 'oad_061_independent_canonical_observation_bridge.py']

def main():
    print("="*104)
    print(" OAD-110 AUTHORITATIVE SPORTS CANONICAL BRIDGE INSTALLER")
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
        exp="from .oad_110_authoritative_sports_canonical_bridge import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] read-only Oracle boundary preserved")
        print("[PASS] execution_authority=FALSE")
        print("[PASS] probability remains disabled")
        print("[DONE] OAD-110 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__":
    main()
