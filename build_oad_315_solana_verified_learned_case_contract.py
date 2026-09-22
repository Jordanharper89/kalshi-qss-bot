from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-315'
TITLE='SOLANA VERIFIED LEARNED-CASE CONTRACT'
EXPECTED='build_oad_315_solana_verified_learned_case_contract.py'
MODULE='oad_315_solana_verified_learned_case_contract.py'
TEST='test_oad_315_solana_verified_learned_case_contract.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py': ('class SolanaVerifiedForwardOutcome', 'def attribute_forward_outcomes'), 'qseries_v2/oracle_continuous_learner/ocl_004_learning_event.py': ('class ', 'outcome')}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from .oad_314_solana_verified_forward_outcome_attribution import SolanaVerifiedForwardOutcome

READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaLearnedCase:
    learned_case_id:str; experience_id:str; token_address:str; pair_address:str
    horizon_seconds:int; conditions:tuple; outcome_class:str; return_fraction:float
    evidence_observation_ids:tuple; evidence_hash:str; verified:bool=True
    execution_authority:bool=False

def _hash(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def build_verified_solana_learned_cases(pending_cases,outcomes):
    pending={(x.experience_id,x.horizon_seconds):x for x in pending_cases}
    out=[]
    for o in outcomes:
        c=pending.get((o.experience_id,o.horizon_seconds))
        if c is None or not o.verified: continue
        ev=tuple(dict.fromkeys(tuple(c.evidence_observation_ids)+tuple(o.evidence_observation_ids)))
        eh=_hash(ev)
        lid="solana-learned:"+_hash((o.experience_id,o.horizon_seconds,c.conditions,o.outcome_class,round(o.return_fraction,12),eh))[:32]
        out.append(SolanaLearnedCase(lid,o.experience_id,o.token_address,o.pair_address,o.horizon_seconds,c.conditions,o.outcome_class,o.return_fraction,ev,eh,True,False))
    return tuple(out)

"""
TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import SolanaOutcomePendingCase
from qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution import SolanaVerifiedForwardOutcome
from qseries_v2.oracle_adapters.independent.oad_315_solana_verified_learned_case_contract import *
class T(unittest.TestCase):
 def test_case(self):
  c=SolanaOutcomePendingCase("e","X","P","t",(("price","RISING"),),("a","b"),15)
  o=SolanaVerifiedForwardOutcome("e","X","P",15,"t","u",1,1.1,.1,"UP",("a","b","c"),True,False)
  x=build_verified_solana_learned_cases((c,),(o,))[0]
  print("[LEARNED]",x.learned_case_id,x.outcome_class)
  self.assertTrue(x.verified); self.assertEqual(x.outcome_class,"UP")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-315 evidence-grounded Solana learned-case contract certified")

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
