
from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-292'
REVISION='OAD_292_SOLANA_BOUNDED_MULTISOURCE_TOKEN_UNIVERSE_V1'
TITLE='SOLANA BOUNDED MULTI-SOURCE TOKEN UNIVERSE'
EXPECTED_FILENAME='build_oad_292_solana_bounded_multisource_token_universe.py'
MODULE_NAME='oad_292_solana_bounded_multisource_token_universe.py'
TEST_NAME='test_oad_292_solana_bounded_multisource_token_universe.py'
DEPENDENCIES=[('oad_262_solana_live_token_discovery.py', 'discover_live_solana_tokens'), ('oad_288_gmgn_clean_acquisition_boundary.py', 'acquire_current_gmgn_token')]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_262_solana_live_token_discovery import discover_live_solana_tokens\nfrom .oad_288_gmgn_clean_acquisition_boundary import acquire_current_gmgn_token\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass SolanaUniverseCandidate:\n    token_address:str\n    sources:tuple\n    dexscreener_payload:dict|None\n    gmgn_payload:dict|None\n\n@dataclass(frozen=True,slots=True)\nclass SolanaBoundedUniverse:\n    candidates:tuple\n    dexscreener_count:int\n    gmgn_count:int\n    unique_tokens:int\n    source_failures:tuple\n    execution_authority:bool=False\n\ndef discover_bounded_multisource_solana_universe(timeout_seconds=30.0):\n    merged={}; failures=[]; dex_count=0; gmgn_count=0\n    try:\n        d=discover_live_solana_tokens(timeout_seconds)\n        for row in tuple(d.payload.get("tokens") or ()):\n            a=str(row.get("token_address") or "").strip()\n            if not a: continue\n            dex_count+=1\n            x=merged.setdefault(a,{"sources":set(),"dex":None,"gmgn":None})\n            x["sources"].add("dexscreener"); x["dex"]=dict(row)\n    except Exception as e:\n        failures.append(("dexscreener",type(e).__name__,str(e)[:240]))\n    try:\n        g=acquire_current_gmgn_token(timeout_seconds=timeout_seconds,candidate_limit=5)\n        a=str(getattr(g,"token_address","") or "").strip()\n        if a:\n            gmgn_count=1\n            x=merged.setdefault(a,{"sources":set(),"dex":None,"gmgn":None})\n            x["sources"].add("gmgn"); x["gmgn"]=dict(getattr(g,"payload",{}) or {})\n    except Exception as e:\n        failures.append(("gmgn",type(e).__name__,str(e)[:240]))\n    if not merged: raise RuntimeError("no Solana universe candidates from certified sources")\n    rows=tuple(SolanaUniverseCandidate(a,tuple(sorted(v["sources"])),v["dex"],v["gmgn"]) for a,v in sorted(merged.items()))\n    return SolanaBoundedUniverse(rows,dex_count,gmgn_count,len(rows),tuple(failures),False)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_292_solana_bounded_multisource_token_universe import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  r=discover_bounded_multisource_solana_universe()\n  print("[PHYSICAL] dexscreener_count=",r.dexscreener_count)\n  print("[PHYSICAL] gmgn_count=",r.gmgn_count)\n  print("[PHYSICAL] unique_tokens=",r.unique_tokens)\n  print("[PHYSICAL] source_failures=",r.source_failures)\n  self.assertGreater(r.unique_tokens,0); self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not z.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-292 bounded multi-source Solana token universe physically certified")\n'
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
