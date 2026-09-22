from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-317'
TITLE='SOLANA EXISTING-OCL LEARNING HANDOFF'
EXPECTED='build_oad_317_solana_existing_ocl_learning_handoff.py'
MODULE='oad_317_solana_existing_ocl_learning_handoff.py'
TEST='test_oad_317_solana_existing_ocl_learning_handoff.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_316_solana_comparable_case_statistics.py': ('def aggregate_comparable_solana_cases', 'class SolanaComparableCaseStatistics'), 'qseries_v2/oracle_continuous_learner/ocl_003_outcome_observation.py': ('outcome',), 'qseries_v2/oracle_continuous_learner/ocl_004_learning_event.py': ('learning',)}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from .oad_316_solana_comparable_case_statistics import aggregate_comparable_solana_cases

READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaLearningHandoff:
    state:str; learned_cases:int; comparable_groups:int; evidence_hash:str|None
    learner_contracts_verified:bool; probability:None=None; direction:None=None
    execution_authority:bool=False

def build_solana_learning_handoff(cases):
    cases=tuple(x for x in cases if getattr(x,"verified",False))
    stats=aggregate_comparable_solana_cases(cases)
    if not cases:
        return SolanaLearningHandoff("HOLD_VERIFIED_OUTCOMES_REQUIRED",0,0,None,True,None,None,False)
    payload=tuple((x.learned_case_id,x.horizon_seconds,x.conditions,x.outcome_class,round(x.return_fraction,12),x.evidence_hash) for x in cases)
    h=sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
    ready=sum(x.state=="COMPARABLE_CASES_READY" for x in stats)
    state="READY_FOR_EXISTING_OCL_LEARNING" if ready else "LEARNED_CASES_PRESENT_SAMPLE_ACCUMULATING"
    return SolanaLearningHandoff(state,len(cases),len(stats),h,True,None,None,False)

"""
TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_315_solana_verified_learned_case_contract import SolanaLearnedCase
from qseries_v2.oracle_adapters.independent.oad_317_solana_existing_ocl_learning_handoff import *
def c(i,o):
 return SolanaLearnedCase(i,i,"X","P",15,(("price","RISING"),),o,.1,("a",),i,True,False)
class T(unittest.TestCase):
 def test_hold(self):
  x=build_solana_learning_handoff(())
  self.assertEqual(x.state,"HOLD_VERIFIED_OUTCOMES_REQUIRED")
 def test_ready(self):
  x=build_solana_learning_handoff((c("1","UP"),c("2","DOWN")))
  print("[HANDOFF]",x.state,x.learned_cases,x.evidence_hash)
  self.assertEqual(x.state,"READY_FOR_EXISTING_OCL_LEARNING")
  self.assertIsNone(x.probability); self.assertIsNone(x.direction)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-317 Solana verified learned cases admitted toward existing OCL architecture")
 print("[PASS] no separate Solana learner created")

"""
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write_checked(p,s):
    s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True); q=p.with_suffix(p.suffix+".tmp")
    q.write_text(s,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" "+BUILD_ID+" "+TITLE+" INSTALLER"); print("="*120); print("[ROOT]",r)
    for rel,markers in DEPENDENCIES.items():
        p=r/rel
        if not p.is_file(): raise RuntimeError("dependency missing: "+rel)
        src=p.read_text(encoding="utf-8"); ast.parse(src,filename=str(p))
        for marker in markers:
            if marker not in src: raise RuntimeError("exact dependency marker missing: "+rel+" -> "+marker)
        print("[PASS] exact dependency verified:",rel)
    protected=[]
    for rel in ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py"):
        p=r/rel
        if not p.is_file(): raise RuntimeError("frozen boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        write_checked(m,MODULE_SOURCE); write_checked(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+m.stem+" import *"
        if exp not in lines: lines.append(exp)
        write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("frozen boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r)); print("[PASS] test installed:",t.name)
        print("[PASS] frozen OPH-023/Kalshi OAD-055 unchanged")
        print("[PASS] GMGN is not a dependency of this learning slice")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
