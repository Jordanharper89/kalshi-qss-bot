
from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-293'
REVISION='OAD_293_SOLANA_TOKEN_POOL_IDENTITY_DEDUP_REGISTRY_V1'
TITLE='SOLANA TOKEN/POOL IDENTITY + DEDUP REGISTRY'
EXPECTED_FILENAME='build_oad_293_solana_token_pool_identity_dedup_registry.py'
MODULE_NAME='oad_293_solana_token_pool_identity_dedup_registry.py'
TEST_NAME='test_oad_293_solana_token_pool_identity_dedup_registry.py'
DEPENDENCIES=[('oad_292_solana_bounded_multisource_token_universe.py', 'discover_bounded_multisource_solana_universe'), ('oad_263_solana_token_pool_identity_liquidity_expansion.py', 'expand_live_solana_token_pools')]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_292_solana_bounded_multisource_token_universe import discover_bounded_multisource_solana_universe\nfrom .oad_263_solana_token_pool_identity_liquidity_expansion import expand_live_solana_token_pools\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass TokenPoolIdentity:\n token_address:str; pair_address:str; dex_id:str|None; base_address:str|None; quote_address:str|None; sources:tuple\n@dataclass(frozen=True,slots=True)\nclass SolanaIdentityRegistry:\n tokens:int; pools:int; identities:tuple; acquisition_failures:tuple; execution_authority:bool=False\ndef build_solana_token_pool_identity_registry(timeout_seconds=30.0,max_tokens=12):\n u=discover_bounded_multisource_solana_universe(timeout_seconds); identities={}; failures=[]\n for c in u.candidates[:max(1,int(max_tokens))]:\n  try:\n   o=expand_live_solana_token_pools(token_address=c.token_address,timeout_seconds=timeout_seconds)\n   if str(o.payload.get("token_address"))!=c.token_address: raise RuntimeError("token identity mismatch")\n   for p in tuple(o.payload.get("pools") or ()):\n    pair=str(p.get("pair_address") or "").strip()\n    if not pair: continue\n    key=(c.token_address,pair)\n    identities[key]=TokenPoolIdentity(c.token_address,pair,p.get("dex_id"),p.get("base_address"),p.get("quote_address"),c.sources)\n  except Exception as e: failures.append((c.token_address,type(e).__name__,str(e)[:200]))\n if not identities: raise RuntimeError("no exact Solana token/pool identities resolved")\n rows=tuple(identities[k] for k in sorted(identities))\n return SolanaIdentityRegistry(len({x.token_address for x in rows}),len(rows),rows,tuple(failures),False)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_293_solana_token_pool_identity_dedup_registry import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  r=build_solana_token_pool_identity_registry(max_tokens=8)\n  print("[PHYSICAL] tokens=",r.tokens); print("[PHYSICAL] pools=",r.pools); print("[PHYSICAL] failures=",r.acquisition_failures)\n  self.assertGreater(r.tokens,0); self.assertGreater(r.pools,0)\n  self.assertEqual(len({(x.token_address,x.pair_address) for x in r.identities}),r.pools)\nif __name__=="__main__":\n z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not z.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-293 deterministic token/pool identity dedup physically certified")\n'
def root():
 for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
  for p in (b,*b.parents):
   if (p/"qseries_v2").is_dir(): return p
 raise RuntimeError("Q Series repository root not found")
def write(path,source):
 s=textwrap.dedent(source).lstrip(); ast.parse(s,filename=str(path)); path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(s,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
 if Path(__file__).name!=EXPECTED_FILENAME: raise RuntimeError("installer identity mismatch")
 r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/MODULE_NAME; test=r/TEST_NAME; init=pkg/"__init__.py"
 print("="*120); print(" "+BUILD_ID+" "+TITLE+" INSTALLER"); print("="*120); print("[ROOT]",r)
 for fn,sym in DEPENDENCIES:
  p=pkg/fn
  if not p.is_file(): raise RuntimeError("dependency missing: "+str(p))
  src=p.read_text(encoding="utf-8"); ast.parse(src,filename=str(p))
  if ("def "+sym+"(") not in src: raise RuntimeError("exact dependency symbol missing: "+fn+" -> "+sym)
  print("[PASS] exact dependency verified:",fn,"->",sym)
 protected=[]
 for p in (r/"qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",r/"qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py"):
  if not p.is_file(): raise RuntimeError("frozen boundary missing: "+str(p))
  protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
 old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
 try:
  write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
  lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []; exp="from ."+module.stem+" import *"
  if exp not in lines: lines.append(exp)
  write(init,"\n".join(x for x in lines if x.strip())+"\n")
  for p,h in protected:
   if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("frozen boundary changed: "+p.name)
  print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.name); print("[PASS] frozen OPH-023/Kalshi OAD-055 unchanged")
  print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE"); print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
 except Exception:
  for p,b in old.items():
   if b is None:
    if p.exists(): p.unlink()
   else: p.write_bytes(b)
  print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
