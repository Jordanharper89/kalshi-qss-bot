from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-264'
REVISION='OAD_264_SOLANA_TOKEN_MINT_AUTHORITY_SUPPLY_INTELLIGENCE_V1'
TITLE='SOLANA TOKEN MINT AUTHORITY AND SUPPLY INTELLIGENCE'
MODULE_NAME='oad_264_solana_token_mint_authority_supply_intelligence.py'
TEST_NAME='test_oad_264_solana_token_mint_authority_supply_intelligence.py'
DEPENDENCIES=['qseries_v2/oracle_adapters/independent/oad_252_crypto_independent_source_expansion_foundation.py', 'qseries_v2/oracle_adapters/independent/oad_263_solana_token_pool_identity_liquidity_expansion.py']
MODULE_SOURCE='\nimport json,urllib.request\nfrom .oad_263_solana_token_pool_identity_liquidity_expansion import expand_live_solana_token_pools\nfrom .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\nRPC="https://api.mainnet.solana.com"\ndef _rpc(method,params,timeout=20.0):\n body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(); req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json","User-Agent":"Oracle-Q-Series/1.0"})\n with urllib.request.urlopen(req,timeout=float(timeout)) as r:d=json.loads(r.read().decode())\n if d.get("error"): raise RuntimeError("Solana RPC error: "+str(d["error"]))\n return d.get("result")\ndef acquire_solana_token_mint_state(token_address=None,timeout_seconds=20.0,rpc=_rpc):\n if token_address is None: token_address=expand_live_solana_token_pools(timeout_seconds=timeout_seconds).payload["token_address"]\n res=rpc("getAccountInfo",[str(token_address),{"encoding":"jsonParsed","commitment":"finalized"}],timeout_seconds); value=(res or {}).get("value")\n if not value: raise RuntimeError("mint account unavailable")\n data=value.get("data") or {}; parsed=data.get("parsed") if isinstance(data,dict) else None; info=(parsed or {}).get("info") or {}\n if not info: raise RuntimeError("mint account not JSON parsed")\n payload={"token_address":str(token_address),"slot":(res or {}).get("context",{}).get("slot"),"program":data.get("program"),"owner_program":value.get("owner"),"decimals":info.get("decimals"),"supply_raw":info.get("supply"),"mint_authority":info.get("mintAuthority"),"freeze_authority":info.get("freezeAuthority"),"is_initialized":info.get("isInitialized")}\n return build_independent_crypto_observation(source_id="source.onchain.solana.mint."+str(token_address),provider="solana_mainnet_rpc",source_class="token_mint_state",subject=str(token_address),observation_type="solana_token_mint_authority_supply",payload=payload)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_264_solana_token_mint_authority_supply_intelligence import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  o=acquire_solana_token_mint_state(); p=o.payload; print("[PHYSICAL] token=",p["token_address"]); print("[PHYSICAL] supply_raw=",p["supply_raw"],"decimals=",p["decimals"]); print("[PHYSICAL] mint_authority=",p["mint_authority"]); print("[PHYSICAL] freeze_authority=",p["freeze_authority"]); self.assertIsNotNone(p["supply_raw"])\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-264 live finalized Solana mint authority/supply intelligence certified")\n'
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
