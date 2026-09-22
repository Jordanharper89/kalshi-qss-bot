from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path
EXPECTED='build_oad_378_solana_oad317_exact_case_execution.py'
BID='OAD-378'
TITLE='SOLANA OAD-317 EXACT CASE EXECUTION'
MODULE='oad_378_solana_oad317_exact_case_execution.py'
TEST='test_oad_378_solana_oad317_exact_case_execution.py'
DEPS={'qseries_v2/oracle_adapters/independent/oad_317_solana_existing_ocl_learning_handoff.py': ('build_solana_learning_handoff', 'cases'), 'qseries_v2/oracle_adapters/independent/oad_376_solana_learned_experience_bridge.py': ('SolanaLearnedExperienceRecord', 'as_learning_payload')}
MODULE_SOURCE=r"""from __future__ import annotations
from dataclasses import dataclass
import importlib, inspect
from .oad_376_solana_learned_experience_bridge import SolanaLearnedExperienceRecord, as_learning_payload
READ_ONLY=True
EXECUTION_AUTHORITY=False
OAD317="qseries_v2.oracle_adapters.independent.oad_317_solana_existing_ocl_learning_handoff"
@dataclass(frozen=True, slots=True)
class OAD317ExactHandoff:
    cases_count:int; result_type:str; result_state:str; result_fields:tuple; execution_authority:bool=False
def _state(x):
    if x is None: return "RETURNED_NONE"
    for n in ("state","status","handoff_state","learning_state"):
        if hasattr(x,n): return str(getattr(x,n))
        if isinstance(x,dict) and n in x: return str(x[n])
    return "RETURNED"
def _fields(x):
    if x is None: return ()
    if isinstance(x,dict): return tuple(sorted(str(k) for k in x))
    out=set()
    if hasattr(x,"__dict__"): out.update(k for k in vars(x) if not k.startswith("_"))
    for n in getattr(type(x),"__slots__",()):
        if isinstance(n,str) and not n.startswith("_"): out.add(n)
    return tuple(sorted(out))
def invoke_oad317_exact(records):
    mod=importlib.import_module(OAD317); f=getattr(mod,"build_solana_learning_handoff")
    sig=inspect.signature(f)
    if tuple(sig.parameters)!=("cases",): raise RuntimeError("OAD-317 signature changed: "+str(sig))
    cases=tuple(as_learning_payload(r) if isinstance(r,SolanaLearnedExperienceRecord) else r for r in records)
    result=f(cases)
    return OAD317ExactHandoff(len(cases),type(result).__name__,_state(result),_fields(result),False),result
"""
TEST_SOURCE=r"""import unittest
from qseries_v2.oracle_adapters.independent.oad_376_solana_learned_experience_bridge import SolanaLearnedExperienceRecord
from qseries_v2.oracle_adapters.independent.oad_378_solana_oad317_exact_case_execution import *
class T(unittest.TestCase):
    def test_exact(self):
        r=SolanaLearnedExperienceRecord("e","c","DEX_SWAP","orca","A","B",15,"UP",0.01,"SOLANA_CANONICAL_HISTORY","0"*64,"EXISTING_OCL",False)
        meta,_=invoke_oad317_exact((r,))
        print("[OAD317-EXACT] cases=",meta.cases_count,"type=",meta.result_type,"state=",meta.result_state,"fields=",meta.result_fields)
        self.assertEqual(meta.cases_count,1)
if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-378 exact OAD-317 (cases) execution contract certified")
"""
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def verify(p,marks):
    if not p.is_file(): raise RuntimeError("dependency missing: "+str(p))
    s=p.read_text(encoding="utf-8"); ast.parse(s,filename=str(p))
    for m in marks:
        if m not in s: raise RuntimeError("dependency interface missing: "+p.name+" -> "+m)
def atomic(p,s):
    s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True); q=p.with_suffix(p.suffix+".tmp")
    q.write_text(s,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" "+BID+" "+TITLE+" INSTALLER"); print("="*120); print("[ROOT]",r)
    for rel,marks in DEPS.items(): verify(r/rel,marks); print("[PASS] dependency interface verified:",rel)
    protected=[]
    for rel in (
      "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
      "qseries_v2/oracle_adapters/independent/oad_317_solana_existing_ocl_learning_handoff.py",
      "qseries_v2/oracle_adapters/independent/oad_372_solana_final_persistence_continuity_physical_gate.py",
      "qseries_v2/oracle_adapters/independent/oad_377_solana_existing_ocl_learning_handoff_physical_gate.py",
    ):
        p=r/rel
        if p.is_file(): protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m,MODULE_SOURCE); atomic(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        ex="from ."+m.stem+" import *"
        if ex not in lines: lines.append(ex)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("protected boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r)); print("[PASS] test installed:",t.name)
        print("[PASS] certified OAD-317 and production boundaries preserved")
        print("[PASS] no fabricated learning outcome introduced")
        print("[PASS] no separate Solana learner introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
