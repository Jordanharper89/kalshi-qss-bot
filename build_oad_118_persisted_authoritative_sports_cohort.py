from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION="OAD_118_PERSISTED_AUTHORITATIVE_SPORTS_COHORT_V1"

def find_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")

def write_py(path,src):
    src=textwrap.dedent(src).lstrip()
    ast.parse(src,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(src,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_118_persisted_authoritative_sports_cohort.py'
TEST=ROOT/'test_oad_118_persisted_authoritative_sports_cohort.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nfrom .oad_115_authoritative_sports_idempotent_persistence import persist_current_authoritative_sports\nfrom .oad_114_authoritative_sports_exact_postgresql_readback import exact_authoritative_sports_readback\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass PersistedAuthoritativeSportsCohort:\n    rows: tuple\n    observation_ids: tuple\n    providers: tuple\n    cohort_size: int\n    committed_new: int\n    execution_authority: bool=False\n\ndef load_persisted_authoritative_sports_cohort(root=None, timeout_seconds=120.0, acquisition_timeout_seconds=20.0):\n    p=persist_current_authoritative_sports(\n        root=root,\n        timeout_seconds=timeout_seconds,\n        acquisition_timeout_seconds=acquisition_timeout_seconds,\n    )\n    ids=tuple(p.observation_ids)\n    rows=tuple(exact_authoritative_sports_readback(ids,root)) if ids else ()\n    if len(rows)!=len(ids):\n        raise RuntimeError("persisted sports cohort exact readback mismatch")\n    for oid,row in zip(ids,rows):\n        if getattr(row,"observation_id",None)!=oid:\n            raise RuntimeError("persisted sports cohort identity mismatch")\n    return PersistedAuthoritativeSportsCohort(\n        rows=rows,\n        observation_ids=ids,\n        providers=tuple(p.providers),\n        cohort_size=len(rows),\n        committed_new=int(p.committed_new),\n        execution_authority=False,\n    )\n'
TEST_SOURCE='import unittest\nfrom unittest.mock import patch\nfrom types import SimpleNamespace\nimport qseries_v2.oracle_adapters.independent.oad_118_persisted_authoritative_sports_cohort as m\n\nclass T(unittest.TestCase):\n    def test_exact_persisted_cohort(self):\n        rows=(SimpleNamespace(observation_id="o1"),SimpleNamespace(observation_id="o2"))\n        p=SimpleNamespace(observation_ids=("o1","o2"),providers=("statsapi.mlb.com",),committed_new=2)\n        with patch.object(m,"persist_current_authoritative_sports",return_value=p), \\\n             patch.object(m,"exact_authoritative_sports_readback",return_value=rows):\n            r=m.load_persisted_authoritative_sports_cohort(root=".")\n        print("[COHORT_SIZE]",r.cohort_size)\n        print("[OBSERVATION_IDS]",r.observation_ids)\n        self.assertEqual(r.cohort_size,2)\n        self.assertEqual(r.observation_ids,("o1","o2"))\n        self.assertFalse(r.execution_authority)\n\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-118 exact persisted authoritative sports cohort certified")\n'
DEPENDENCIES=['oad_115_authoritative_sports_idempotent_persistence.py', 'oad_114_authoritative_sports_exact_postgresql_readback.py']

def main():
    print("="*112)
    print(" OAD-118 PERSISTED AUTHORITATIVE SPORTS COHORT INSTALLER")
    print("="*112)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)
    for dep in DEPENDENCIES:
        p=PKG/dep
        if not p.is_file(): raise RuntimeError("Required certified dependency missing: "+str(p))
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}
    try:
        write_py(MODULE,MODULE_SOURCE)
        write_py(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from .oad_118_persisted_authoritative_sports_cohort import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] existing certified boundaries preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-118 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__":
    main()
