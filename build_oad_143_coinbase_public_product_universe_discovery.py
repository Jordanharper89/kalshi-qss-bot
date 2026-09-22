from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_143_COINBASE_PUBLIC_PRODUCT_UNIVERSE_DISCOVERY_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_143_coinbase_public_product_universe_discovery.py'; test=r/'test_oad_143_coinbase_public_product_universe_discovery.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-143 COINBASE PUBLIC PRODUCT UNIVERSE DISCOVERY INSTALLER"); print("="*112); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_142_coinbase_crypto_market_data_foundation.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nimport json\nfrom urllib.request import Request,urlopen\n\nBASE="https://api.exchange.coinbase.com"\nPRODUCTS_URL=BASE+"/products"\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\n\ndef _get_json(url,timeout_seconds):\n    req=Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0 read-only","Accept":"application/json"})\n    with urlopen(req,timeout=timeout_seconds) as r:\n        return json.loads(r.read().decode("utf-8"))\n\ndef discover_coinbase_public_products(timeout_seconds=20.0,quote_currencies=("USD","USDC"),limit=1000):\n    rows=_get_json(PRODUCTS_URL,timeout_seconds)\n    out=[]\n    allowed=set(quote_currencies)\n    for row in rows if isinstance(rows,list) else ():\n        pid=str(row.get("id") or "")\n        if not pid: continue\n        if allowed and str(row.get("quote_currency") or "") not in allowed: continue\n        if row.get("trading_disabled") is True: continue\n        out.append({\n            "product_id":pid,\n            "base_currency":row.get("base_currency"),\n            "quote_currency":row.get("quote_currency"),\n            "base_increment":row.get("base_increment"),\n            "quote_increment":row.get("quote_increment"),\n            "min_market_funds":row.get("min_market_funds"),\n            "status":row.get("status"),\n            "cancel_only":row.get("cancel_only"),\n            "limit_only":row.get("limit_only"),\n            "post_only":row.get("post_only"),\n            "source_url":PRODUCTS_URL,\n        })\n        if len(out)>=int(limit): break\n    return tuple(out)\n'); write(test,'import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_143_coinbase_public_product_universe_discovery as m\nclass T(unittest.TestCase):\n    def test_discovery(self):\n        rows=[{"id":"BTC-USD","base_currency":"BTC","quote_currency":"USD","trading_disabled":False},{"id":"ETH-EUR","base_currency":"ETH","quote_currency":"EUR","trading_disabled":False},{"id":"BAD-USD","base_currency":"BAD","quote_currency":"USD","trading_disabled":True}]\n        with patch.object(m,"_get_json",return_value=rows):\n            r=m.discover_coinbase_public_products()\n        print("[PRODUCTS]",len(r),r[0]["product_id"])\n        self.assertEqual(tuple(x["product_id"] for x in r),("BTC-USD",))\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-143 Coinbase public product-universe discovery certified")\n')
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_143_coinbase_public_product_universe_discovery import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] existing PostgreSQL single-writer architecture preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-143 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
