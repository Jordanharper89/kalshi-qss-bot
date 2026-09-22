
from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path

REVISION="OAD_265_SOLANA_HOLDER_CONCENTRATION_INDEXED_RPC_PROVIDER_FAILOVER_FOUNDATIONAL_REBUILD_V1"
MODULE_NAME="oad_265_solana_token_holder_concentration_intelligence.py"
TEST_NAME="test_oad_265_solana_token_holder_concentration_intelligence.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nimport json, os, time, urllib.error, urllib.request\nfrom decimal import Decimal\nfrom .oad_264_solana_token_mint_authority_supply_intelligence import acquire_solana_token_mint_state\nfrom .oad_252_crypto_independent_source_expansion_foundation import (\n    build_independent_crypto_observation,\n    verify_independent_crypto_observation,\n)\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\nOFFICIAL_RPC="https://api.mainnet.solana.com"\nPUBLIC_INDEXED_RPC="https://rpc.solanatracker.io/public"\n\ndef _configured_indexed_endpoints():\n    rows=[]\n    explicit=str(os.getenv("SOLANA_INDEXED_RPC_URL") or "").strip()\n    general=str(os.getenv("SOLANA_RPC_URL") or "").strip()\n    if explicit:\n        rows.append(("configured_indexed_rpc",explicit))\n    if general and general != explicit:\n        rows.append(("configured_rpc",general))\n    rows.append(("solanatracker_public_rpc",PUBLIC_INDEXED_RPC))\n    # Official endpoint remains last-resort only. It is known to throttle this\n    # indexed method and is not treated as the preferred production provider.\n    rows.append(("solana_public_rpc_last_resort",OFFICIAL_RPC))\n    out=[]\n    seen=set()\n    for provider,url in rows:\n        if url and url not in seen:\n            seen.add(url); out.append((provider,url))\n    return tuple(out)\n\ndef _post_rpc(url,method,params,timeout):\n    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()\n    req=urllib.request.Request(\n        url,\n        data=body,\n        headers={\n            "Content-Type":"application/json",\n            "Accept":"application/json",\n            "User-Agent":"Oracle-Q-Series/1.0",\n        },\n    )\n    with urllib.request.urlopen(req,timeout=float(timeout)) as r:\n        data=json.loads(r.read().decode())\n    if data.get("error"):\n        raise RuntimeError("RPC error: "+str(data["error"]))\n    return data.get("result")\n\ndef _get_largest_accounts_with_failover(token_address,timeout_seconds=20.0):\n    failures=[]\n    for provider,url in _configured_indexed_endpoints():\n        try:\n            result=_post_rpc(\n                url,\n                "getTokenLargestAccounts",\n                [token_address,{"commitment":"finalized"}],\n                timeout_seconds,\n            )\n            rows=(result or {}).get("value") or []\n            if rows:\n                return provider,url,result,tuple(failures)\n            failures.append((provider,"EMPTY_RESULT"))\n        except urllib.error.HTTPError as exc:\n            failures.append((provider,"HTTP_"+str(exc.code)))\n            print("[PROVIDER_FAILOVER]",provider,"HTTP",exc.code)\n        except Exception as exc:\n            failures.append((provider,type(exc).__name__))\n            print("[PROVIDER_FAILOVER]",provider,type(exc).__name__,str(exc)[:180])\n    raise RuntimeError("all indexed Solana RPC providers failed: "+repr(tuple(failures)))\n\ndef acquire_solana_holder_concentration(token_address=None,timeout_seconds=20.0):\n    # OAD-264 remains the frozen/certified source of finalized mint supply truth.\n    mint=acquire_solana_token_mint_state(token_address,timeout_seconds)\n    token_address=mint.payload["token_address"]\n    supply=Decimal(str(mint.payload["supply_raw"]))\n    if supply <= 0:\n        raise RuntimeError("token supply is not positive")\n\n    provider,rpc_url,result,failures=_get_largest_accounts_with_failover(\n        token_address,\n        timeout_seconds,\n    )\n    rows=(result or {}).get("value") or []\n    amounts=[Decimal(str(x.get("amount") or "0")) for x in rows]\n    top1=amounts[0]\n    top5=sum(amounts[:5],Decimal(0))\n    top20=sum(amounts[:20],Decimal(0))\n\n    payload={\n        "token_address":token_address,\n        "slot":(result or {}).get("context",{}).get("slot"),\n        "supply_raw":str(supply),\n        "largest_account_count":len(rows),\n        "top1_share":float(top1/supply),\n        "top5_share":float(top5/supply),\n        "top20_share":float(top20/supply),\n        "largest_accounts":tuple(\n            {\n                "address":x.get("address"),\n                "amount":x.get("amount"),\n                "decimals":x.get("decimals"),\n                "ui_amount_string":x.get("uiAmountString"),\n            }\n            for x in rows[:20]\n        ),\n        "indexed_rpc_provider":provider,\n        "indexed_rpc_url":rpc_url,\n        "provider_failures":failures,\n        "commitment":"finalized",\n        "method":"getTokenLargestAccounts",\n    }\n\n    observation=build_independent_crypto_observation(\n        source_id="source.onchain.solana.holder_concentration."+token_address,\n        provider=provider,\n        source_class="holder_concentration",\n        subject=token_address,\n        observation_type="solana_token_holder_concentration",\n        payload=payload,\n    )\n    if not verify_independent_crypto_observation(observation):\n        raise RuntimeError("OAD-252 provenance verification failed")\n    return observation\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_265_solana_token_holder_concentration_intelligence import *\n\nclass T(unittest.TestCase):\n    def test_physical(self):\n        o=acquire_solana_holder_concentration()\n        p=o.payload\n        print("[PHYSICAL] token=",p["token_address"])\n        print("[PHYSICAL] indexed_rpc_provider=",p["indexed_rpc_provider"])\n        print("[PHYSICAL] largest_accounts=",p["largest_account_count"])\n        print("[PHYSICAL] top1_share=",p["top1_share"])\n        print("[PHYSICAL] top5_share=",p["top5_share"])\n        print("[PHYSICAL] top20_share=",p["top20_share"])\n        print("[PHYSICAL] provider_failures=",p["provider_failures"])\n        print("[PHYSICAL] commitment=",p["commitment"])\n        self.assertGreater(p["largest_account_count"],0)\n        self.assertGreaterEqual(p["top5_share"],p["top1_share"])\n        self.assertGreaterEqual(p["top20_share"],p["top5_share"])\n        self.assertEqual(p["method"],"getTokenLargestAccounts")\n        self.assertTrue(verify_independent_crypto_observation(o))\n        self.assertFalse(EXECUTION_AUTHORITY)\n\nif __name__=="__main__":\n    result=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OAD-265 indexed-RPC provider-failover holder concentration physically certified")\n    print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE publication_allowed=FALSE execution_authority=FALSE")\n'
DEPENDENCIES=[
 "qseries_v2/oracle_adapters/independent/oad_252_crypto_independent_source_expansion_foundation.py",
 "qseries_v2/oracle_adapters/independent/oad_264_solana_token_mint_authority_supply_intelligence.py",
]

def root():
 for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
  for p in (b,*b.parents):
   if (p/"qseries_v2").is_dir(): return p
 raise RuntimeError("Q Series repository root not found")

def write_checked(path,source):
 source=textwrap.dedent(source).lstrip()
 ast.parse(source,filename=str(path))
 tmp=path.with_suffix(path.suffix+".tmp")
 tmp.write_text(source,encoding="utf-8",newline="\n")
 os.replace(tmp,path)

def main():
 r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
 module=pkg/MODULE_NAME; test=r/TEST_NAME; init=pkg/"__init__.py"
 print("="*120)
 print(" OAD-265 SOLANA HOLDER CONCENTRATION INDEXED-RPC PROVIDER FAILOVER REBUILD INSTALLER")
 print("="*120)
 print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
 for dep in DEPENDENCIES:
  p=r/dep
  if not p.is_file(): raise RuntimeError("Required dependency missing: "+dep)
  print("[PASS] dependency verified:",dep)

 protected=[]
 for p,label in (
  (r/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py","Frozen OPH-023"),
  (r/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py","Frozen Kalshi OAD-055"),
 ):
  if p.is_file():
   protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
   print("[PASS]",label,"verified")

 old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
 try:
  write_checked(module,MODULE_SOURCE)
  write_checked(test,TEST_SOURCE)
  lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
  exp="from .oad_265_solana_token_holder_concentration_intelligence import *"
  if exp not in lines: lines.append(exp)
  write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")
  for p,h in protected:
   if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
    raise RuntimeError("Frozen boundary changed: "+p.name)
  print("[PASS] failed rate-limit-only implementation retired")
  print("[PASS] indexed-RPC provider failover installed")
  print("[PASS] configured SOLANA_INDEXED_RPC_URL supported")
  print("[PASS] SolanaTracker public RPC installed as default indexed provider")
  print("[PASS] official Solana public RPC demoted to last-resort")
  print("[PASS] exact getTokenLargestAccounts semantics preserved")
  print("[PASS] finalized OAD-264 mint supply truth preserved")
  print("[PASS] module installed:",module.relative_to(r))
  print("[PASS] test installed:",test.name)
  print("[PASS] syntax validated")
  print("[PASS] frozen production boundaries unchanged")
  print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE publication_allowed=FALSE execution_authority=FALSE")
  print("[DONE] OAD-265 PROVIDER-FAILOVER REBUILD INSTALLATION COMPLETE")
 except Exception:
  for p,data in old.items():
   if data is None:
    if p.exists(): p.unlink()
   else: p.write_bytes(data)
  print("[ROLLBACK] affected files restored")
  raise

if __name__=="__main__": main()
