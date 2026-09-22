from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-313'
TITLE='SOLANA OUTCOME-PENDING TEMPORAL CASES'
EXPECTED='build_oad_313_solana_outcome_pending_temporal_cases.py'
MODULE='oad_313_solana_outcome_pending_temporal_cases.py'
TEST='test_oad_313_solana_outcome_pending_temporal_cases.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_271_solana_historical_experience_formation.py': ('def build_solana_historical_experiences', 'outcome_attached:bool=False'), 'qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py': ('TEMPORAL_5_15_30_60_READY',)}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .oad_271_solana_historical_experience_formation import build_solana_historical_experiences

READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaOutcomePendingCase:
    experience_id:str; token_address:str; pair_address:str; snapshot_at:str
    conditions:tuple; evidence_observation_ids:tuple; horizon_seconds:int
    state:str="OUTCOME_PENDING"; execution_authority:bool=False

def build_outcome_pending_solana_cases(records,horizons=(15,30,60)):
    out=[]
    for x in build_solana_historical_experiences(records):
        for h in tuple(int(v) for v in horizons if int(v)>0):
            out.append(SolanaOutcomePendingCase(
                x.experience_id,x.token_address,x.pair_address,x.snapshot_at,
                x.conditions,x.evidence_observation_ids,h,"OUTCOME_PENDING",False
            ))
    return tuple(out)

"""
TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_267_solana_pool_liquidity_historical_state import SolanaHistoricalObservation
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import *
def row(i,t,p):
    return SolanaHistoricalObservation(i,"S","solana_token_pool_identity_liquidity",t,None,"dex","X",
      {"token_address":"X","pools":({"pair_address":"P","liquidity_usd":100+p*10,"buys_h24":10+p,"sells_h24":8,"volume_h24":100+p*10,"price_usd":p},)})
class T(unittest.TestCase):
    def test_cases(self):
        x=build_outcome_pending_solana_cases((row("a","2026-09-01T00:00:00+00:00",1.0),row("b","2026-09-01T00:00:05+00:00",1.1)))
        print("[CASES]",len(x),tuple(c.horizon_seconds for c in x))
        self.assertEqual(tuple(c.horizon_seconds for c in x),(15,30,60))
        self.assertTrue(all(c.state=="OUTCOME_PENDING" for c in x))
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-313 Solana temporal cases formed without fabricating outcomes")

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
