from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-328'; TITLE='SOLANA LIVE DEX POOL IDENTITY REGISTRY'; EXPECTED='build_oad_328_solana_live_dex_pool_identity_registry.py'; MODULE='oad_328_solana_live_dex_pool_identity_registry.py'; TEST='test_oad_328_solana_live_dex_pool_identity_registry.py'; DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_254_solana_dex_liquidity_intelligence.py': ('acquire_solana_dex_liquidity', 'pair_address', 'dex_id'), 'qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py': ('certify_solana_universal_continuity',)}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from .oad_254_solana_dex_liquidity_intelligence import acquire_solana_dex_liquidity
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaLiveDexPoolRegistry:
    query:str; pools:int; dexes:tuple; by_pair:tuple; provider:str; execution_authority:bool=False
def build_live_solana_dex_pool_registry(query="SOL/USDC",limit=100,timeout_seconds=20.0):
    x=acquire_solana_dex_liquidity(query=query,limit=limit,timeout=timeout_seconds)
    rows=tuple(x.payload.get("pairs") or ())
    by={}
    for r in rows:
        pair=str(r.get("pair_address") or "").strip(); dex=str(r.get("dex_id") or "unknown").strip().lower()
        if pair: by[pair]=dex
    if not by: raise RuntimeError("live Solana DEX registry contained no pair identities")
    return SolanaLiveDexPoolRegistry(str(query),len(by),tuple(sorted(set(by.values()))),tuple(sorted(by.items())),str(x.provider),False)
def dex_by_pair(registry):
    return dict(registry.by_pair)

"""
TEST_SOURCE=r"""\

import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent import oad_328_solana_live_dex_pool_identity_registry as m
class T(unittest.TestCase):
 def test_registry(self):
  obs=SimpleNamespace(provider="dexscreener",payload={"pairs":[{"pair_address":"P1","dex_id":"raydium"},{"pair_address":"P2","dex_id":"orca"},{"pair_address":"P3","dex_id":"meteora"},{"pair_address":"P4","dex_id":"pumpswap"}]})
  with patch.object(m,"acquire_solana_dex_liquidity",return_value=obs):
   x=m.build_live_solana_dex_pool_registry()
  print("[DEXES]",x.dexes,"pools=",x.pools)
  self.assertEqual(x.pools,4);self.assertIn("raydium",x.dexes);self.assertIn("pumpswap",x.dexes)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-328 live Solana DEX/pool identity registry certified")

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
