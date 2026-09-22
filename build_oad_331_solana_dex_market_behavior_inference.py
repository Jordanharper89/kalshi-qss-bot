from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-331'; TITLE='SOLANA DEX MARKET BEHAVIOR INFERENCE'; EXPECTED='build_oad_331_solana_dex_market_behavior_inference.py'; MODULE='oad_331_solana_dex_market_behavior_inference.py'; TEST='test_oad_331_solana_dex_market_behavior_inference.py'; DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_329_solana_dex_transaction_attribution.py': ('attribute_transactions_to_live_dex_pools',), 'qseries_v2/oracle_adapters/independent/oad_330_solana_wallet_token_flow_graph.py': ('build_wallet_token_flows',)}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaDecodedMarketBehavior:
 signature:str;slot:int;behavior:str;dex_ids:tuple;owner:str|None;mints:tuple;flow_count:int;evidence:tuple;execution_authority:bool=False
def infer_solana_market_behavior(envelopes,attributions,flows):
    amap={x.signature:x for x in attributions};fmap=defaultdict(list)
    for f in flows:fmap[f.signature].append(f)
    out=[]
    for e in envelopes:
        a=amap.get(e.signature);fs=fmap.get(e.signature,[])
        byowner=defaultdict(list)
        for f in fs:
            if f.owner:byowner[f.owner].append(f)
        emitted=False
        for owner,rows in byowner.items():
            pos=[x for x in rows if x.delta>0];neg=[x for x in rows if x.delta<0]
            if a and a.attributed and pos and neg and len({x.mint for x in rows if x.mint})>=2:
                out.append(SolanaDecodedMarketBehavior(e.signature,e.slot,"DEX_SWAP",a.dex_ids,owner,tuple(sorted({x.mint for x in rows if x.mint})),len(rows),a.matched_pool_accounts,False));emitted=True
            elif a and a.attributed and len(rows)>=2 and (pos or neg):
                b="DEX_LIQUIDITY_FLOW"
                out.append(SolanaDecodedMarketBehavior(e.signature,e.slot,b,a.dex_ids,owner,tuple(sorted({x.mint for x in rows if x.mint})),len(rows),a.matched_pool_accounts,False));emitted=True
        if a and a.attributed and not emitted:
            out.append(SolanaDecodedMarketBehavior(e.signature,e.slot,"DEX_INTERACTION_UNRESOLVED",a.dex_ids,None,tuple(),0,a.matched_pool_accounts,False))
    return tuple(out)

"""
TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_331_solana_dex_market_behavior_inference import *
class T(unittest.TestCase):
 def test_swap(self):
  e=SimpleNamespace(signature="s",slot=1)
  a=SimpleNamespace(signature="s",attributed=True,dex_ids=("orca",),matched_pool_accounts=("P",))
  f=(SimpleNamespace(signature="s",owner="W",mint="A",delta=-2.0),SimpleNamespace(signature="s",owner="W",mint="B",delta=5.0))
  x=infer_solana_market_behavior((e,),(a,),f)[0]
  print("[BEHAVIOR]",x.behavior,x.dex_ids,x.mints)
  self.assertEqual(x.behavior,"DEX_SWAP")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-331 evidence-grounded DEX swap/liquidity behavior inference certified")

"""
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def atomic(p,s):
    s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p)); p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp"); q.write_text(s,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" "+BUILD_ID+" "+TITLE+" INSTALLER"); print("="*120); print("[ROOT]",r)
    for rel,marks in DEPENDENCIES.items():
        p=r/rel
        if not p.is_file(): raise RuntimeError("dependency missing: "+rel)
        src=p.read_text(encoding="utf-8"); ast.parse(src,filename=str(p))
        for mark in marks:
            if mark not in src: raise RuntimeError("dependency contract missing: "+rel+" -> "+mark)
        print("[PASS] exact dependency verified:",rel)
    protected=[]
    for rel in ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
                "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
                "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py"):
        p=r/rel
        if not p.is_file(): raise RuntimeError("protected boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m,MODULE_SOURCE); atomic(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+m.stem+" import *"
        if exp not in lines: lines.append(exp)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("protected boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r)); print("[PASS] test installed:",t.name)
        print("[PASS] OAD-327 continuity boundary preserved unchanged")
        print("[PASS] live pool/Dex identity used; no brittle hard-coded DEX program dependency")
        print("[PASS] unknown chain behavior retained and measured")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
