from __future__ import annotations
import json
from urllib.parse import quote
from urllib.request import Request,urlopen
from .oad_142_coinbase_crypto_market_data_foundation import build_coinbase_market_observation,utcnow_iso,validate_coinbase_market_observation
from .oad_143_coinbase_public_product_universe_discovery import discover_coinbase_public_products,BASE

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False

def _get_json(url,timeout_seconds):
    req=Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0 read-only","Accept":"application/json"})
    with urlopen(req,timeout=timeout_seconds) as r:
        return json.loads(r.read().decode("utf-8"))

def acquire_coinbase_live_spot_observations(timeout_seconds=20.0,max_products=25):
    products=discover_coinbase_public_products(timeout_seconds=timeout_seconds,limit=max_products)
    out=[]
    for p in products:
        pid=p["product_id"]
        url=BASE+"/products/"+quote(pid,safe="")+"/ticker"
        try:
            row=_get_json(url,timeout_seconds)
        except Exception:
            continue
        if not isinstance(row,dict) or row.get("price") in (None,""): continue
        payload={
            "product_id":pid,
            "price":row.get("price"),
            "bid":row.get("bid"),
            "ask":row.get("ask"),
            "volume":row.get("volume"),
            "trade_id":row.get("trade_id"),
            "time":row.get("time"),
            "base_currency":p.get("base_currency"),
            "quote_currency":p.get("quote_currency"),
        }
        o=build_coinbase_market_observation(
            source_id=f"coinbase:{pid}:ticker:{row.get('trade_id') or row.get('time') or 'latest'}",
            crypto_family="spot",observation_type="live_ticker",subject=pid,
            observed_at=str(row.get("time") or utcnow_iso()),source_url=url,payload=payload)
        if not validate_coinbase_market_observation(o): raise RuntimeError("Coinbase observation validation failed")
        out.append(o)
    return tuple(out)
