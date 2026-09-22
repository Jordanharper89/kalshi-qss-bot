from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-316'
TITLE='SOLANA COMPARABLE-CASE STATISTICS'
EXPECTED='build_oad_316_solana_comparable_case_statistics.py'
MODULE='oad_316_solana_comparable_case_statistics.py'
TEST='test_oad_316_solana_comparable_case_statistics.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_315_solana_verified_learned_case_contract.py': ('class SolanaLearnedCase', 'def build_verified_solana_learned_cases')}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from math import exp

READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaComparableCaseStatistics:
    horizon_seconds:int; conditions:tuple; sample_size:int; effective_sample_size:float
    up_count:int; down_count:int; flat_count:int; raw_up_frequency:float
    weighted_up_frequency:float; contradictions:int; state:str
    execution_authority:bool=False

def aggregate_comparable_solana_cases(cases,half_life_cases=100.0):
    groups={}
    for c in cases:
        if not c.verified: continue
        groups.setdefault((c.horizon_seconds,tuple(c.conditions)),[]).append(c)
    out=[]
    for (h,cond),rows in sorted(groups.items(),key=lambda x:(x[0][0],str(x[0][1]))):
        n=len(rows); up=sum(x.outcome_class=="UP" for x in rows); down=sum(x.outcome_class=="DOWN" for x in rows); flat=n-up-down
        weights=[exp(-max(0,n-1-i)*0.6931471805599453/max(1.0,float(half_life_cases))) for i in range(n)]
        total=sum(weights); wup=sum(w for w,x in zip(weights,rows) if x.outcome_class=="UP")
        contradictions=min(up,down)
        out.append(SolanaComparableCaseStatistics(h,cond,n,total,up,down,flat,up/n,wup/total if total else 0.0,contradictions,"COMPARABLE_CASES_READY" if n>=2 else "INSUFFICIENT_SAMPLE",False))
    return tuple(out)

"""
TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_315_solana_verified_learned_case_contract import SolanaLearnedCase
from qseries_v2.oracle_adapters.independent.oad_316_solana_comparable_case_statistics import *
def c(i,outcome):
 return SolanaLearnedCase(i,i,"X","P",15,(("price","RISING"),),outcome,.1,("a",),i,True,False)
class T(unittest.TestCase):
 def test_stats(self):
  x=aggregate_comparable_solana_cases((c("1","UP"),c("2","UP"),c("3","DOWN")))[0]
  print("[STATS] samples=",x.sample_size,"raw_up=",x.raw_up_frequency,"weighted_up=",x.weighted_up_frequency,"contradictions=",x.contradictions)
  self.assertEqual(x.sample_size,3); self.assertEqual(x.up_count,2); self.assertEqual(x.contradictions,1)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-316 Solana comparable-case frequencies + recency weighting certified")

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
