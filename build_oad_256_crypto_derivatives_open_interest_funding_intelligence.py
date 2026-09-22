
from __future__ import annotations
import ast, os, textwrap, subprocess, sys
from pathlib import Path

BUILD_ID='OAD-256'
TITLE='CRYPTO DERIVATIVES OPEN-INTEREST FUNDING INTELLIGENCE'
REVISION='OAD_256_CRYPTO_DERIVATIVES_OPEN_INTEREST_FUNDING_INTELLIGENCE_V1'
MODULE_NAME='oad_256_crypto_derivatives_open_interest_funding_intelligence.py'
TEST_NAME='test_oad_256_crypto_derivatives_open_interest_funding_intelligence.py'
DEPENDENCIES=['qseries_v2/oracle_adapters/independent/oad_252_crypto_independent_source_expansion_foundation.py']
MODULE_SOURCE='\nimport json, urllib.parse, urllib.request\nfrom .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\nBASE="https://api.bybit.com/v5/market/tickers"\ndef _get(url,timeout=15.0):\n req=urllib.request.Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0","Accept":"application/json"})\n with urllib.request.urlopen(req,timeout=float(timeout)) as r: return json.loads(r.read().decode())\ndef acquire_derivatives_state(symbol="BTCUSDT",timeout=15.0,fetch=_get):\n s=str(symbol).upper()\n d=fetch(BASE+"?"+urllib.parse.urlencode({"category":"linear","symbol":s}),timeout)\n if int(d.get("retCode",-1))!=0: raise RuntimeError("derivatives provider rejected request")\n rows=((d.get("result") or {}).get("list") or [])\n if not rows: raise RuntimeError("derivatives ticker unavailable")\n x=rows[0]\n payload={"symbol":s,"last_price":x.get("lastPrice"),"mark_price":x.get("markPrice"),"index_price":x.get("indexPrice"),"open_interest":x.get("openInterest"),"open_interest_value":x.get("openInterestValue"),"funding_rate":x.get("fundingRate"),"next_funding_time":x.get("nextFundingTime"),"volume_24h":x.get("volume24h"),"turnover_24h":x.get("turnover24h")}\n return build_independent_crypto_observation(source_id="source.derivatives.bybit."+s.lower(),provider="bybit_public_market",source_class="derivatives_state",subject=s,observation_type="open_interest_funding",payload=payload)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_256_crypto_derivatives_open_interest_funding_intelligence import *\nclass T(unittest.TestCase):\n def test_derivatives(self):\n  def f(url,timeout): return {"retCode":0,"result":{"list":[{"lastPrice":"100","markPrice":"99","indexPrice":"98","openInterest":"10","openInterestValue":"1000","fundingRate":"0.0001","nextFundingTime":"1","volume24h":"20","turnover24h":"2000"}]}}\n  x=acquire_derivatives_state(fetch=f); print("[DERIVATIVES]",x.payload["open_interest"],x.payload["funding_rate"]); self.assertEqual(x.payload["symbol"],"BTCUSDT")\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-256 derivatives open-interest/funding intelligence certified")\n'

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
