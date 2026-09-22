
from __future__ import annotations
import ast, os, textwrap, subprocess, sys
from pathlib import Path

BUILD_ID='OAD-254'
TITLE='SOLANA DEX LIQUIDITY INTELLIGENCE'
REVISION='OAD_254_SOLANA_DEX_LIQUIDITY_INTELLIGENCE_V1'
MODULE_NAME='oad_254_solana_dex_liquidity_intelligence.py'
TEST_NAME='test_oad_254_solana_dex_liquidity_intelligence.py'
DEPENDENCIES=['qseries_v2/oracle_adapters/independent/oad_252_crypto_independent_source_expansion_foundation.py', 'qseries_v2/oracle_adapters/independent/oad_151_solana_onchain_physical_runtime_certification.py']
MODULE_SOURCE='\nimport json, urllib.parse, urllib.request\nfrom .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\nBASE="https://api.dexscreener.com/latest/dex/search"\ndef _get(url,timeout=15.0):\n req=urllib.request.Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0","Accept":"application/json"})\n with urllib.request.urlopen(req,timeout=float(timeout)) as r: return json.loads(r.read().decode())\ndef acquire_solana_dex_liquidity(query="SOL/USDC",limit=25,timeout=15.0,fetch=_get):\n d=fetch(BASE+"?q="+urllib.parse.quote(str(query)),timeout)\n pairs=[p for p in (d.get("pairs") or []) if str(p.get("chainId") or "").lower()=="solana"][:max(1,int(limit))]\n if not pairs: raise RuntimeError("no Solana DEX pairs returned")\n rows=[]\n for p in pairs:\n  liq=p.get("liquidity") or {}; vol=p.get("volume") or {}; tx=p.get("txns") or {}\n  rows.append({"dex_id":p.get("dexId"),"pair_address":p.get("pairAddress"),"base":(p.get("baseToken") or {}).get("address"),"quote":(p.get("quoteToken") or {}).get("address"),"price_usd":p.get("priceUsd"),"liquidity_usd":liq.get("usd"),"volume_h24":vol.get("h24"),"txns_h24":tx.get("h24"),"pair_created_at":p.get("pairCreatedAt")})\n return build_independent_crypto_observation(source_id="source.dex.solana.search."+str(query).lower().replace("/","_"),provider="dexscreener",source_class="dex_liquidity",subject=str(query),observation_type="solana_dex_pairs",payload={"pairs":rows,"pair_count":len(rows)})\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_254_solana_dex_liquidity_intelligence import *\nclass T(unittest.TestCase):\n def test_dex(self):\n  def f(url,timeout): return {"pairs":[{"chainId":"solana","dexId":"x","pairAddress":"p","baseToken":{"address":"b"},"quoteToken":{"address":"q"},"priceUsd":"1","liquidity":{"usd":1000},"volume":{"h24":500},"txns":{"h24":{"buys":2,"sells":1}}}]}\n  x=acquire_solana_dex_liquidity(fetch=f); print("[PAIRS]",x.payload["pair_count"]); self.assertEqual(x.payload["pair_count"],1)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-254 Solana DEX liquidity intelligence certified")\n'

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
