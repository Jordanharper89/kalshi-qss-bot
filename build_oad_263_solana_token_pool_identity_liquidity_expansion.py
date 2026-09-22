from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-263'
REVISION='OAD_263_SOLANA_TOKEN_POOL_IDENTITY_LIQUIDITY_EXPANSION_V1'
TITLE='SOLANA TOKEN POOL IDENTITY AND LIQUIDITY EXPANSION'
MODULE_NAME='oad_263_solana_token_pool_identity_liquidity_expansion.py'
TEST_NAME='test_oad_263_solana_token_pool_identity_liquidity_expansion.py'
DEPENDENCIES=['qseries_v2/oracle_adapters/independent/oad_252_crypto_independent_source_expansion_foundation.py', 'qseries_v2/oracle_adapters/independent/oad_262_solana_live_token_discovery.py']
MODULE_SOURCE='\nimport json,urllib.request,urllib.parse\nfrom .oad_262_solana_live_token_discovery import discover_live_solana_tokens\nfrom .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\nBASE="https://api.dexscreener.com/token-pairs/v1/solana/"\ndef _get(url,timeout=20.0):\n req=urllib.request.Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0","Accept":"application/json"})\n with urllib.request.urlopen(req,timeout=float(timeout)) as r:return json.loads(r.read().decode())\ndef expand_live_solana_token_pools(token_address=None,timeout_seconds=20.0,fetch=_get):\n if token_address is None: token_address=discover_live_solana_tokens(timeout_seconds).payload["tokens"][0]["token_address"]\n rows=fetch(BASE+urllib.parse.quote(str(token_address),safe=""),timeout_seconds)\n if not isinstance(rows,list): raise RuntimeError("token-pairs response invalid")\n pools=[]\n for p in rows:\n  if str(p.get("chainId") or "").lower()!="solana" or not p.get("pairAddress"): continue\n  tx=p.get("txns") or {}; h24=tx.get("h24") or {}; liq=p.get("liquidity") or {}; vol=p.get("volume") or {}; pc=p.get("priceChange") or {}\n  pools.append({"pair_address":p.get("pairAddress"),"dex_id":p.get("dexId"),"base_address":(p.get("baseToken") or {}).get("address"),"base_symbol":(p.get("baseToken") or {}).get("symbol"),"quote_address":(p.get("quoteToken") or {}).get("address"),"quote_symbol":(p.get("quoteToken") or {}).get("symbol"),"price_usd":p.get("priceUsd"),"liquidity_usd":liq.get("usd"),"volume_h24":vol.get("h24"),"buys_h24":h24.get("buys"),"sells_h24":h24.get("sells"),"price_change_h24":pc.get("h24"),"fdv":p.get("fdv"),"market_cap":p.get("marketCap"),"pair_created_at":p.get("pairCreatedAt")})\n if not pools: raise RuntimeError("no live Solana pools for discovered token")\n return build_independent_crypto_observation(source_id="source.dex.solana.token_pools."+str(token_address),provider="dexscreener",source_class="token_pool_liquidity",subject=str(token_address),observation_type="solana_token_pool_identity_liquidity",payload={"token_address":str(token_address),"pools":tuple(pools),"pool_count":len(pools)})\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_263_solana_token_pool_identity_liquidity_expansion import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  o=expand_live_solana_token_pools(); p=o.payload["pools"][0]; print("[PHYSICAL] token=",o.payload["token_address"]); print("[PHYSICAL] pool_count=",o.payload["pool_count"]); print("[PHYSICAL] first_pool=",p["pair_address"],p["dex_id"],p["base_symbol"],p["quote_symbol"]); self.assertGreater(o.payload["pool_count"],0)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-263 live Solana token/pool identity and liquidity expansion certified")\n'
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
