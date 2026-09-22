from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-262'
REVISION='OAD_262_SOLANA_LIVE_TOKEN_DISCOVERY_V1'
TITLE='SOLANA LIVE TOKEN DISCOVERY'
MODULE_NAME='oad_262_solana_live_token_discovery.py'
TEST_NAME='test_oad_262_solana_live_token_discovery.py'
DEPENDENCIES=['qseries_v2/oracle_adapters/independent/oad_252_crypto_independent_source_expansion_foundation.py', 'qseries_v2/oracle_adapters/independent/oad_261_universal_expansion_source_single_writer_postgresql_persistence.py']
MODULE_SOURCE='\nimport json,urllib.request\nfrom .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation,verify_independent_crypto_observation\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\nENDPOINTS=("https://api.dexscreener.com/token-profiles/latest/v1","https://api.dexscreener.com/token-boosts/latest/v1","https://api.dexscreener.com/token-boosts/top/v1")\ndef _get(url,timeout=20.0):\n req=urllib.request.Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0","Accept":"application/json"})\n with urllib.request.urlopen(req,timeout=float(timeout)) as r:return json.loads(r.read().decode())\ndef discover_live_solana_tokens(timeout_seconds=20.0,fetch=_get):\n seen={}; failures=[]\n for url in ENDPOINTS:\n  try:\n   d=fetch(url,timeout_seconds); rows=d if isinstance(d,list) else [d]\n   for x in rows:\n    if isinstance(x,dict) and str(x.get("chainId") or "").lower()=="solana" and x.get("tokenAddress"):\n     a=str(x["tokenAddress"]); seen.setdefault(a,{"token_address":a,"profile_url":x.get("url"),"description":x.get("description"),"links":x.get("links") or [],"discovery_endpoint":url})\n  except Exception as e: failures.append((url,type(e).__name__))\n if not seen: raise RuntimeError("no live Solana token identities discovered")\n o=build_independent_crypto_observation(source_id="source.dex.solana.token_discovery.latest",provider="dexscreener",source_class="token_discovery",subject="SOLANA",observation_type="solana_live_token_discovery",payload={"tokens":tuple(seen.values()),"token_count":len(seen),"endpoint_failures":tuple(failures)})\n if not verify_independent_crypto_observation(o): raise RuntimeError("provenance verification failed")\n return o\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_262_solana_live_token_discovery import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  o=discover_live_solana_tokens(); print("[PHYSICAL] token_count=",o.payload["token_count"]); print("[PHYSICAL] first_token=",o.payload["tokens"][0]["token_address"]); print("[PHYSICAL] endpoint_failures=",o.payload["endpoint_failures"]); self.assertGreater(o.payload["token_count"],0)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-262 live Solana token discovery physically certified")\n'
def root():
 for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
  for p in (b,*b.parents):
   if (p/"qseries_v2").is_dir(): return p
 raise RuntimeError("Q Series repository root not found")
def write(path,source):
 source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path)); path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
 r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/MODULE_NAME; test=r/TEST_NAME; init=pkg/"__init__.py"
 print("="*120); print(" "+BUILD_ID+" "+TITLE+" INSTALLER"); print("="*120); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
 for dep in DEPENDENCIES:
  p=r/dep
  if not p.is_file(): raise RuntimeError("Required dependency missing: "+dep)
  print("[PASS] dependency verified:",dep)
 protected=[]
 for p,label in ((r/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py","Frozen OPH-023"),(r/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py","Frozen Kalshi OAD-055")):
  if p.is_file(): protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest())); print("[PASS]",label,"verified")
 old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
 try:
  write(module,MODULE_SOURCE); write(test,TEST_SOURCE); lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []; exp="from ."+module.stem+" import *"
  if exp not in lines: lines.append(exp)
  write(init,"\n".join(x for x in lines if x.strip())+"\n")
  for p,h in protected:
   if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("Frozen boundary changed: "+p.name)
  print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.name); print("[PASS] syntax validated"); print("[PASS] frozen production boundaries unchanged"); print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE publication_allowed=FALSE execution_authority=FALSE"); print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
 except Exception:
  for p,data in old.items():
   if data is None:
    if p.exists(): p.unlink()
   else: p.write_bytes(data)
  print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
