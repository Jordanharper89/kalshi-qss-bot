from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-314'
TITLE='SOLANA VERIFIED FORWARD OUTCOME ATTRIBUTION'
EXPECTED='build_oad_314_solana_verified_forward_outcome_attribution.py'
MODULE='oad_314_solana_verified_forward_outcome_attribution.py'
TEST='test_oad_314_solana_verified_forward_outcome_attribution.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_313_solana_outcome_pending_temporal_cases.py': ('class SolanaOutcomePendingCase', 'def build_outcome_pending_solana_cases'), 'qseries_v2/oracle_adapters/independent/oad_267_solana_pool_liquidity_historical_state.py': ('class SolanaHistoricalObservation',)}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from .oad_313_solana_outcome_pending_temporal_cases import SolanaOutcomePendingCase

READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaVerifiedForwardOutcome:
    experience_id:str; token_address:str; pair_address:str; horizon_seconds:int
    anchor_at:str; outcome_at:str; anchor_price:float; outcome_price:float
    return_fraction:float; outcome_class:str; evidence_observation_ids:tuple
    verified:bool=True; execution_authority:bool=False

def _dt(v): return datetime.fromisoformat(str(v).replace("Z","+00:00"))
def _price_for_pair(record,pair):
    for p in tuple(record.payload.get("pools") or ()):
        if str(p.get("pair_address") or "")==str(pair):
            try:return float(p.get("price_usd"))
            except (TypeError,ValueError):return None
    return None

def attribute_forward_outcomes(cases,records,tolerance_seconds=8.0):
    rows=tuple(sorted(records,key=lambda r:_dt(r.observed_at)))
    out=[]
    for c in cases:
        anchor_t=_dt(c.snapshot_at); target=anchor_t.timestamp()+c.horizon_seconds
        anchor_candidates=[r for r in rows if r.observation_id in set(c.evidence_observation_ids)]
        if not anchor_candidates: continue
        anchor=anchor_candidates[-1]; ap=_price_for_pair(anchor,c.pair_address)
        candidates=[r for r in rows if _dt(r.observed_at).timestamp()>=target and _dt(r.observed_at).timestamp()<=target+float(tolerance_seconds)]
        for r in candidates:
            op=_price_for_pair(r,c.pair_address)
            if ap is None or op is None or ap==0: continue
            ret=(op-ap)/ap
            cls="UP" if ret>0 else "DOWN" if ret<0 else "FLAT"
            out.append(SolanaVerifiedForwardOutcome(c.experience_id,c.token_address,c.pair_address,c.horizon_seconds,c.snapshot_at,r.observed_at,ap,op,ret,cls,tuple(c.evidence_observation_ids)+(r.observation_id,),True,False))
            break
    return tuple(out)

"""
TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_267_solana_pool_liquidity_historical_state import SolanaHistoricalObservation
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import SolanaOutcomePendingCase
from qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution import *
def row(i,t,p):
 return SolanaHistoricalObservation(i,"S","solana_token_pool_identity_liquidity",t,None,"dex","X",{"token_address":"X","pools":({"pair_address":"P","price_usd":p},)})
class T(unittest.TestCase):
 def test_outcome(self):
  c=SolanaOutcomePendingCase("e","X","P","2026-09-01T00:00:05+00:00",(("price","RISING"),),("a","b"),15)
  x=attribute_forward_outcomes((c,),(row("a","2026-09-01T00:00:00+00:00",1),row("b","2026-09-01T00:00:05+00:00",1.1),row("c","2026-09-01T00:00:20+00:00",1.21)))
  print("[OUTCOME]",x[0].outcome_class,x[0].return_fraction)
  self.assertTrue(x[0].verified); self.assertEqual(x[0].outcome_class,"UP")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-314 exact future-observation Solana outcome attribution certified")

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
