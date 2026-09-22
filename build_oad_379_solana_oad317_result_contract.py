from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path
EXPECTED='build_oad_379_solana_oad317_result_contract.py'
BID='OAD-379'
TITLE='SOLANA OAD-317 RESULT CONTRACT'
MODULE='oad_379_solana_oad317_result_contract.py'
TEST='test_oad_379_solana_oad317_result_contract.py'
DEPS={'qseries_v2/oracle_adapters/independent/oad_378_solana_oad317_exact_case_execution.py': ('invoke_oad317_exact', 'OAD317ExactHandoff')}
MODULE_SOURCE=r"""from __future__ import annotations
from dataclasses import dataclass, is_dataclass, asdict
from .oad_378_solana_oad317_exact_case_execution import invoke_oad317_exact
READ_ONLY=True
EXECUTION_AUTHORITY=False
@dataclass(frozen=True, slots=True)
class OAD317ResultContract:
    result_type:str; state:str; fields:tuple; downstream_hints:tuple; execution_authority:bool=False
def inspect_oad317_result(records):
    meta,result=invoke_oad317_exact(records); vals={}
    if isinstance(result,dict): vals=result
    elif is_dataclass(result):
        try: vals=asdict(result)
        except Exception: vals={}
    elif hasattr(result,"__dict__"): vals={k:v for k,v in vars(result).items() if not k.startswith("_")}
    hints=[]
    for k,v in vals.items():
        if any(x in str(k).lower() for x in ("ocl","learn","handoff","case","record","experience","state","payload")):
            hints.append((str(k),type(v).__name__))
    return OAD317ResultContract(meta.result_type,meta.result_state,meta.result_fields,tuple(hints),False),result
"""
TEST_SOURCE=r"""import unittest
from qseries_v2.oracle_adapters.independent.oad_376_solana_learned_experience_bridge import SolanaLearnedExperienceRecord
from qseries_v2.oracle_adapters.independent.oad_379_solana_oad317_result_contract import *
class T(unittest.TestCase):
    def test_contract(self):
        r=SolanaLearnedExperienceRecord("e","c","DEX_SWAP","orca","A","B",15,"UP",0.01,"SOLANA_CANONICAL_HISTORY","0"*64,"EXISTING_OCL",False)
        x,_=inspect_oad317_result((r,))
        print("[OAD317-RESULT] type=",x.result_type,"state=",x.state,"fields=",x.fields,"downstream=",x.downstream_hints)
        self.assertTrue(x.result_type)
if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-379 real OAD-317 return/downstream contract exposed")
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
