from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-307'
TITLE='SOLANA TEMPORAL MARKET CONDITION PROFILE'
EXPECTED='build_oad_307_solana_temporal_market_condition_profile.py'
MODULE='oad_307_solana_temporal_market_condition_profile.py'
TEST='test_oad_307_solana_temporal_market_condition_profile.py'
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_267_solana_pool_liquidity_historical_state.py', ('def read_solana_proven_history', 'class SolanaHistoryReadback')), ('qseries_v2/oracle_adapters/independent/oad_270_solana_price_volume_liquidity_acceleration_conditions.py', ('def build_solana_acceleration_conditions', 'class SolanaAccelerationCondition'))]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_267_solana_pool_liquidity_historical_state import read_solana_proven_history\nfrom .oad_270_solana_price_volume_liquidity_acceleration_conditions import build_solana_acceleration_conditions\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass TemporalMarketConditionProfile:\n    token_address:str; queried_rows:int; pair_conditions:tuple; ready_pairs:int; evidence_state:str; probability:None=None; direction:None=None; execution_authority:bool=False\ndef build_current_temporal_market_condition_profile(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):\n    h=read_solana_proven_history(root=root,refresh=True,timeout_seconds=timeout_seconds,acquisition_timeout_seconds=acquisition_timeout_seconds)\n    token=str(h.current_token_address or "")\n    if not token: raise RuntimeError("current Solana token identity missing")\n    rows=tuple(r for r in h.records if str(r.payload.get("token_address") or r.subject or "")==token)\n    conditions=build_solana_acceleration_conditions(rows); ready=sum(1 for x in conditions if x.state=="COMPOSITE_READY")\n    state="TEMPORAL_READY" if conditions and ready else "TEMPORAL_PARTIAL"\n    return TemporalMarketConditionProfile(token,h.queried_rows,conditions,ready,state,None,None,False)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_307_solana_temporal_market_condition_profile import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  x=build_current_temporal_market_condition_profile()\n  print("[PHYSICAL] token=",x.token_address); print("[PHYSICAL] queried_rows=",x.queried_rows); print("[PHYSICAL] pair_conditions=",len(x.pair_conditions)); print("[PHYSICAL] ready_pairs=",x.ready_pairs); print("[PHYSICAL] evidence_state=",x.evidence_state)\n  self.assertTrue(x.token_address); self.assertGreaterEqual(x.queried_rows,1); self.assertIsNone(x.probability); self.assertIsNone(x.direction); self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-307 temporal Solana market conditions physically certified without prediction")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(p,s):
    s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p)); p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp"); q.write_text(s,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer filename identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" "+BUILD_ID+" "+TITLE+" INSTALLER"); print("="*120); print("[ROOT]",r)
    for rel,marks in DEPENDENCIES:
        p=r/rel
        if not p.is_file(): raise RuntimeError("dependency missing: "+rel)
        s=p.read_text(encoding="utf-8"); ast.parse(s,filename=str(p))
        for mark in marks:
            if mark not in s: raise RuntimeError("exact dependency marker missing: "+rel+" -> "+mark)
        print("[PASS] exact dependency verified:",rel)
    protected=[]
    for rel in ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py"):
        p=r/rel
        if not p.is_file(): raise RuntimeError("frozen boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        write(m,MODULE_SOURCE); write(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []; exp="from ."+m.stem+" import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("frozen boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r)); print("[PASS] test installed:",t.name)
        print("[PASS] frozen OPH-023/Kalshi OAD-055 unchanged")
        print("[PASS] source identity and evidence class remain explicit; no cross-token blending")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
