
from __future__ import annotations
import ast, os, textwrap, subprocess, sys
from pathlib import Path

BUILD_ID='OAD-253'
TITLE='COINBASE EXCHANGE LIQUIDITY ORDER-BOOK INTELLIGENCE'
REVISION='OAD_253_COINBASE_EXCHANGE_LIQUIDITY_ORDER_BOOK_INTELLIGENCE_V1'
MODULE_NAME='oad_253_coinbase_exchange_liquidity_orderbook_intelligence.py'
TEST_NAME='test_oad_253_coinbase_exchange_liquidity_orderbook_intelligence.py'
DEPENDENCIES=['qseries_v2/oracle_adapters/independent/oad_252_crypto_independent_source_expansion_foundation.py', 'qseries_v2/oracle_adapters/independent/oad_144_coinbase_live_spot_market_acquisition.py']
MODULE_SOURCE='\nimport json, urllib.request\nfrom .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\nBASE="https://api.exchange.coinbase.com"\ndef _get(url,timeout=15.0):\n req=urllib.request.Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0","Accept":"application/json"})\n with urllib.request.urlopen(req,timeout=float(timeout)) as r: return json.loads(r.read().decode())\ndef acquire_coinbase_orderbook(product_id="BTC-USD",level=2,timeout=15.0,fetch=_get):\n p=str(product_id).upper()\n if level not in (1,2): raise ValueError("public read-only levels 1 or 2 only")\n d=fetch(f"{BASE}/products/{p}/book?level={level}",timeout)\n bids=d.get("bids") or []; asks=d.get("asks") or []\n if not bids or not asks: raise RuntimeError("Coinbase order book empty")\n bp=float(bids[0][0]); ap=float(asks[0][0])\n payload={"product_id":p,"sequence":d.get("sequence"),"best_bid":bp,"best_ask":ap,"spread":ap-bp,"bid_levels":len(bids),"ask_levels":len(asks),"level":level}\n return build_independent_crypto_observation(source_id="source.exchange.coinbase.orderbook."+p.lower(),provider="coinbase_exchange",source_class="exchange_liquidity",subject=p,observation_type="l2_orderbook",payload=payload)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_253_coinbase_exchange_liquidity_orderbook_intelligence import *\nclass T(unittest.TestCase):\n def test_book(self):\n  def f(url,timeout): return {"sequence":9,"bids":[["100","2",1]],"asks":[["101","3",1]]}\n  x=acquire_coinbase_orderbook(fetch=f); print("[BOOK]",x.payload); self.assertEqual(x.payload["spread"],1.0)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-253 Coinbase order-book intelligence certified")\n'

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
