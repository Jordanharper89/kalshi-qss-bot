from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION="OAD_114_AUTHORITATIVE_SPORTS_EXACT_POSTGRESQL_READBACK_V1"

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
MODULE=PKG/'oad_114_authoritative_sports_exact_postgresql_readback.py'
TEST=ROOT/'test_oad_114_authoritative_sports_exact_postgresql_readback.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\n\nfrom .oad_068_exact_postgresql_independent_readback import (\n    _backend as _existing_backend,\n    _query_one as _existing_query_one,\n    exact_postgresql_readback as _existing_exact_readback,\n)\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\ndef find_authoritative_sports_observation(observation_id, root=None, index=0):\n    backend=_existing_backend(root)\n    return _existing_query_one(backend,str(observation_id),int(index))\n\ndef exact_authoritative_sports_readback(observation_ids, root=None):\n    return _existing_exact_readback(tuple(str(x) for x in observation_ids),root)\n'
TEST_SOURCE='import unittest\nfrom unittest.mock import patch\nfrom types import SimpleNamespace\n\nimport qseries_v2.oracle_adapters.independent.oad_114_authoritative_sports_exact_postgresql_readback as m\n\nclass T(unittest.TestCase):\n    def test_exact_reader_reuses_oad068(self):\n        row=SimpleNamespace(observation_id="obs-1")\n        with patch.object(m,"_existing_backend",return_value=object()) as b, \\\n             patch.object(m,"_existing_query_one",return_value=row) as q:\n            got=m.find_authoritative_sports_observation("obs-1",root=".")\n        print("[OBSERVATION_ID]",got.observation_id)\n        b.assert_called_once()\n        q.assert_called_once()\n        self.assertEqual(got.observation_id,"obs-1")\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-114 exact PostgreSQL readback reuse certified")\n'
DEPENDENCIES=['oad_068_exact_postgresql_independent_readback.py']

def main():
    print("="*112)
    print(" OAD-114 AUTHORITATIVE SPORTS EXACT POSTGRESQL READBACK INSTALLER")
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
        exp="from .oad_114_authoritative_sports_exact_postgresql_readback import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] existing certified architecture reused")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-114 INSTALLATION COMPLETE")
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
