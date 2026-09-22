from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-265'
REVISION='OAD_265_SOLANA_TOKEN_HOLDER_CONCENTRATION_INTELLIGENCE_V1'
TITLE='SOLANA TOKEN HOLDER CONCENTRATION INTELLIGENCE'
MODULE_NAME='oad_265_solana_token_holder_concentration_intelligence.py'
TEST_NAME='test_oad_265_solana_token_holder_concentration_intelligence.py'
DEPENDENCIES=['qseries_v2/oracle_adapters/independent/oad_252_crypto_independent_source_expansion_foundation.py', 'qseries_v2/oracle_adapters/independent/oad_264_solana_token_mint_authority_supply_intelligence.py']
MODULE_SOURCE='\nimport json,urllib.request\nfrom decimal import Decimal\nfrom .oad_264_solana_token_mint_authority_supply_intelligence import acquire_solana_token_mint_state\nfrom .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\nRPC="https://api.mainnet.solana.com"\ndef _rpc(method,params,timeout=20.0):\n body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(); req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json","User-Agent":"Oracle-Q-Series/1.0"})\n with urllib.request.urlopen(req,timeout=float(timeout)) as r:d=json.loads(r.read().decode())\n if d.get("error"): raise RuntimeError("Solana RPC error: "+str(d["error"]))\n return d.get("result")\ndef acquire_solana_holder_concentration(token_address=None,timeout_seconds=20.0,rpc=_rpc):\n mint=acquire_solana_token_mint_state(token_address,timeout_seconds,rpc); token_address=mint.payload["token_address"]; supply=Decimal(str(mint.payload["supply_raw"]))\n res=rpc("getTokenLargestAccounts",[token_address,{"commitment":"finalized"}],timeout_seconds); rows=(res or {}).get("value") or []\n if not rows or supply<=0: raise RuntimeError("largest-account concentration unavailable")\n amounts=[Decimal(str(x.get("amount") or "0")) for x in rows]; top1=amounts[0]; top5=sum(amounts[:5],Decimal(0)); top20=sum(amounts[:20],Decimal(0))\n payload={"token_address":token_address,"slot":(res or {}).get("context",{}).get("slot"),"supply_raw":str(supply),"largest_account_count":len(rows),"top1_share":float(top1/supply),"top5_share":float(top5/supply),"top20_share":float(top20/supply),"largest_accounts":tuple({"address":x.get("address"),"amount":x.get("amount")} for x in rows[:20])}\n return build_independent_crypto_observation(source_id="source.onchain.solana.holder_concentration."+token_address,provider="solana_mainnet_rpc",source_class="holder_concentration",subject=token_address,observation_type="solana_token_holder_concentration",payload=payload)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_265_solana_token_holder_concentration_intelligence import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  o=acquire_solana_holder_concentration(); p=o.payload; print("[PHYSICAL] token=",p["token_address"]); print("[PHYSICAL] largest_accounts=",p["largest_account_count"]); print("[PHYSICAL] top1_share=",p["top1_share"]); print("[PHYSICAL] top5_share=",p["top5_share"]); print("[PHYSICAL] top20_share=",p["top20_share"]); self.assertGreater(p["largest_account_count"],0)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-265 live Solana holder concentration intelligence certified")\n'
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
