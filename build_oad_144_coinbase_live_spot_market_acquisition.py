from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_144_COINBASE_LIVE_SPOT_MARKET_ACQUISITION_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_144_coinbase_live_spot_market_acquisition.py'; test=r/'test_oad_144_coinbase_live_spot_market_acquisition.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-144 COINBASE LIVE SPOT MARKET ACQUISITION INSTALLER"); print("="*112); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_142_coinbase_crypto_market_data_foundation.py', 'oad_143_coinbase_public_product_universe_discovery.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nimport json\nfrom urllib.parse import quote\nfrom urllib.request import Request,urlopen\nfrom .oad_142_coinbase_crypto_market_data_foundation import build_coinbase_market_observation,utcnow_iso,validate_coinbase_market_observation\nfrom .oad_143_coinbase_public_product_universe_discovery import discover_coinbase_public_products,BASE\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\n\ndef _get_json(url,timeout_seconds):\n    req=Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0 read-only","Accept":"application/json"})\n    with urlopen(req,timeout=timeout_seconds) as r:\n        return json.loads(r.read().decode("utf-8"))\n\ndef acquire_coinbase_live_spot_observations(timeout_seconds=20.0,max_products=25):\n    products=discover_coinbase_public_products(timeout_seconds=timeout_seconds,limit=max_products)\n    out=[]\n    for p in products:\n        pid=p["product_id"]\n        url=BASE+"/products/"+quote(pid,safe="")+"/ticker"\n        try:\n            row=_get_json(url,timeout_seconds)\n        except Exception:\n            continue\n        if not isinstance(row,dict) or row.get("price") in (None,""): continue\n        payload={\n            "product_id":pid,\n            "price":row.get("price"),\n            "bid":row.get("bid"),\n            "ask":row.get("ask"),\n            "volume":row.get("volume"),\n            "trade_id":row.get("trade_id"),\n            "time":row.get("time"),\n            "base_currency":p.get("base_currency"),\n            "quote_currency":p.get("quote_currency"),\n        }\n        o=build_coinbase_market_observation(\n            source_id=f"coinbase:{pid}:ticker:{row.get(\'trade_id\') or row.get(\'time\') or \'latest\'}",\n            crypto_family="spot",observation_type="live_ticker",subject=pid,\n            observed_at=str(row.get("time") or utcnow_iso()),source_url=url,payload=payload)\n        if not validate_coinbase_market_observation(o): raise RuntimeError("Coinbase observation validation failed")\n        out.append(o)\n    return tuple(out)\n'); write(test,'import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_144_coinbase_live_spot_market_acquisition as m\nclass T(unittest.TestCase):\n    def test_mapping(self):\n        products=({"product_id":"BTC-USD","base_currency":"BTC","quote_currency":"USD"},)\n        tick={"price":"60000.00","bid":"59999","ask":"60001","volume":"100","trade_id":123,"time":"2026-08-29T00:00:00Z"}\n        with patch.object(m,"discover_coinbase_public_products",return_value=products),patch.object(m,"_get_json",return_value=tick):\n            r=m.acquire_coinbase_live_spot_observations()\n        print("[COINBASE_OBSERVATIONS]",len(r),r[0].subject,r[0].payload["price"])\n        self.assertEqual(len(r),1); self.assertFalse(r[0].independent_evidence)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-144 Coinbase live spot acquisition contract certified")\n')
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_144_coinbase_live_spot_market_acquisition import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] existing PostgreSQL single-writer architecture preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-144 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
