
from __future__ import annotations
import ast, os, textwrap, subprocess, sys
from pathlib import Path

BUILD_ID='OAD-255'
TITLE='SOLANA STABLECOIN SUPPLY INTELLIGENCE'
REVISION='OAD_255_SOLANA_STABLECOIN_SUPPLY_INTELLIGENCE_V1'
MODULE_NAME='oad_255_solana_stablecoin_supply_intelligence.py'
TEST_NAME='test_oad_255_solana_stablecoin_supply_intelligence.py'
DEPENDENCIES=['qseries_v2/oracle_adapters/independent/oad_252_crypto_independent_source_expansion_foundation.py', 'qseries_v2/oracle_adapters/independent/oad_148_solana_mainnet_chain_state_acquisition.py']
MODULE_SOURCE='\nimport json, urllib.request\nfrom .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\nRPC="https://api.mainnet.solana.com"\nMINTS={"USDC":"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v","USDT":"Es9vMFrzaCERmJfrF4H2FYD1zJ9xZK9gP8VfQJ7i2gX"}\ndef _rpc(method,params,timeout=15.0):\n body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()\n req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json","User-Agent":"Oracle-Q-Series/1.0"})\n with urllib.request.urlopen(req,timeout=float(timeout)) as r: return json.loads(r.read().decode())\ndef acquire_solana_stablecoin_supply(symbol="USDC",timeout=15.0,rpc=_rpc):\n s=str(symbol).upper()\n if s not in MINTS: raise ValueError("unsupported certified stablecoin mint")\n d=rpc("getTokenSupply",[MINTS[s],{"commitment":"finalized"}],timeout)\n v=((d.get("result") or {}).get("value") or {})\n if not v.get("amount"): raise RuntimeError("Solana token supply unavailable")\n payload={"symbol":s,"mint":MINTS[s],"amount_raw":v.get("amount"),"decimals":v.get("decimals"),"ui_amount_string":v.get("uiAmountString")}\n return build_independent_crypto_observation(source_id="source.onchain.solana.stablecoin."+s.lower(),provider="solana_mainnet_rpc",source_class="stablecoin_supply",subject=s,observation_type="finalized_token_supply",payload=payload)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_255_solana_stablecoin_supply_intelligence import *\nclass T(unittest.TestCase):\n def test_supply(self):\n  def r(method,params,timeout): return {"result":{"value":{"amount":"1000000","decimals":6,"uiAmountString":"1"}}}\n  x=acquire_solana_stablecoin_supply(rpc=r); print("[STABLECOIN]",x.payload); self.assertEqual(x.payload["symbol"],"USDC")\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-255 Solana stablecoin supply intelligence certified")\n'

def root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def atomic(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp,path)

def main():
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/MODULE_NAME
    test=r/TEST_NAME
    init=pkg/"__init__.py"
    print("="*120); print(" "+BUILD_ID+" "+TITLE+" INSTALLER"); print("="*120)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in DEPENDENCIES:
        p=r/dep
        if not p.is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        atomic(module,MODULE_SOURCE); atomic(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+module.stem+" import *"
        if exp not in lines: lines.append(exp)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.name)
        print("[PASS] syntax validated")
        p=subprocess.run([sys.executable,str(test)],cwd=str(r))
        if p.returncode: raise RuntimeError("Certification test failed: "+test.name)
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation failed; affected files restored")
        raise
    print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE publication_allowed=FALSE execution_authority=FALSE")
    print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
if __name__=="__main__": main()
