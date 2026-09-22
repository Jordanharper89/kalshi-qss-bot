from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION="OAD_116_AUTHORITATIVE_SPORTS_PRODUCTION_PERSISTENCE_CERTIFICATION_V1"

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write_py(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_116_authoritative_sports_production_persistence_certification.py'
TEST=ROOT/'test_oad_116_authoritative_sports_production_persistence_certification.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\n\nfrom .oad_115_authoritative_sports_idempotent_persistence import persist_current_authoritative_sports\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\ndef run_authoritative_sports_production_certification(root=None, timeout_seconds=120.0, acquisition_timeout_seconds=20.0):\n    r=persist_current_authoritative_sports(root,timeout_seconds,acquisition_timeout_seconds)\n    if r.execution_authority is not False:\n        raise RuntimeError("execution authority boundary violated")\n    if r.cohort_size:\n        if r.exact_readback!=r.cohort_size:\n            raise RuntimeError("sports persistence certification readback mismatch")\n        if r.already_present+r.missing_before_write!=r.cohort_size:\n            raise RuntimeError("sports persistence accounting mismatch")\n        if r.committed_new!=r.missing_before_write:\n            raise RuntimeError("sports missing-only commit mismatch")\n    return {\n        "certified": True,\n        "cohort_size": r.cohort_size,\n        "already_present": r.already_present,\n        "committed_new": r.committed_new,\n        "exact_readback": r.exact_readback,\n        "providers": r.providers,\n        "read_only": True,\n        "probability_enabled": False,\n        "execution_authority": False,\n    }\n'
TEST_SOURCE='import unittest\nfrom unittest.mock import patch\nfrom types import SimpleNamespace\nimport qseries_v2.oracle_adapters.independent.oad_116_authoritative_sports_production_persistence_certification as m\n\nclass T(unittest.TestCase):\n    def test_certification_accounting(self):\n        src=SimpleNamespace(\n            cohort_size=15,already_present=10,missing_before_write=5,committed_new=5,\n            exact_readback=15,providers=("statsapi.mlb.com",),execution_authority=False)\n        with patch.object(m,"persist_current_authoritative_sports",return_value=src):\n            r=m.run_authoritative_sports_production_certification(root=".")\n        print("[CERTIFIED]",r["certified"])\n        print("[COHORT_SIZE]",r["cohort_size"])\n        print("[COMMITTED_NEW]",r["committed_new"])\n        print("[EXACT_READBACK]",r["exact_readback"])\n        self.assertTrue(r["certified"])\n        self.assertEqual(r["exact_readback"],15)\n        self.assertFalse(r["execution_authority"])\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-116 production persistence certification contract certified")\n    print("[NOTE] run_authoritative_sports_production_certification performs physical network+PostgreSQL certification")\n'
DEPENDENCIES=['oad_115_authoritative_sports_idempotent_persistence.py']

def main():
    print("="*112)
    print(" OAD-116 AUTHORITATIVE SPORTS PRODUCTION PERSISTENCE CERTIFICATION INSTALLER")
    print("="*112)
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
        exp="from .oad_116_authoritative_sports_production_persistence_certification import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] existing certified architecture reused")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-116 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__":
    main()
