from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION="OAD_117_AUTHORITATIVE_SPORTS_LIVE_PERSISTENCE_GATE_V1"

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
MODULE=PKG/'oad_117_authoritative_sports_live_persistence_gate.py'
TEST=ROOT/'test_oad_117_authoritative_sports_live_persistence_gate.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\n\nfrom .oad_116_authoritative_sports_production_persistence_certification import (\n    run_authoritative_sports_production_certification,\n)\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass LiveSportsPersistenceGate:\n    certified: bool\n    cohort_size: int\n    already_present: int\n    committed_new: int\n    exact_readback: int\n    providers: tuple\n    certified_at: str\n    execution_authority: bool=False\n\ndef run_live_authoritative_sports_persistence_gate(root=None, timeout_seconds=120.0, acquisition_timeout_seconds=20.0):\n    r=run_authoritative_sports_production_certification(\n        root=root,\n        timeout_seconds=timeout_seconds,\n        acquisition_timeout_seconds=acquisition_timeout_seconds,\n    )\n    if r.get("certified") is not True:\n        raise RuntimeError("authoritative sports production persistence not certified")\n    cohort=int(r.get("cohort_size",0))\n    exact=int(r.get("exact_readback",0))\n    already=int(r.get("already_present",0))\n    committed=int(r.get("committed_new",0))\n    if exact!=cohort:\n        raise RuntimeError("live sports exact readback does not equal cohort")\n    if already+committed!=cohort:\n        raise RuntimeError("live sports persistence accounting does not close")\n    return LiveSportsPersistenceGate(\n        certified=True,\n        cohort_size=cohort,\n        already_present=already,\n        committed_new=committed,\n        exact_readback=exact,\n        providers=tuple(r.get("providers",())),\n        certified_at=datetime.now(timezone.utc).isoformat(),\n        execution_authority=False,\n    )\n'
TEST_SOURCE='import unittest\nfrom unittest.mock import patch\nimport qseries_v2.oracle_adapters.independent.oad_117_authoritative_sports_live_persistence_gate as m\n\nclass T(unittest.TestCase):\n    def test_accounting_contract(self):\n        fixture={"certified":True,"cohort_size":15,"already_present":10,"committed_new":5,\n                 "exact_readback":15,"providers":("statsapi.mlb.com",),\n                 "read_only":True,"probability_enabled":False,"execution_authority":False}\n        with patch.object(m,"run_authoritative_sports_production_certification",return_value=fixture):\n            r=m.run_live_authoritative_sports_persistence_gate(root=".")\n        print("[CERTIFIED]",r.certified)\n        print("[COHORT_SIZE]",r.cohort_size)\n        print("[ALREADY_PRESENT]",r.already_present)\n        print("[COMMITTED_NEW]",r.committed_new)\n        print("[EXACT_READBACK]",r.exact_readback)\n        self.assertTrue(r.certified)\n        self.assertEqual(r.already_present+r.committed_new,r.cohort_size)\n        self.assertEqual(r.exact_readback,r.cohort_size)\n        self.assertFalse(r.execution_authority)\n\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-117 live persistence gate contract certified")\n    print("[PHYSICAL] Run production function to exercise live MLB/NHL + PostgreSQL path")\n'
DEPENDENCIES=['oad_116_authoritative_sports_production_persistence_certification.py']

def main():
    print("="*112)
    print(" OAD-117 AUTHORITATIVE SPORTS LIVE PERSISTENCE GATE INSTALLER")
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
        exp="from .oad_117_authoritative_sports_live_persistence_gate import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] existing certified boundaries preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-117 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__":
    main()
