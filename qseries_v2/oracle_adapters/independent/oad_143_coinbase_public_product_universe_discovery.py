from __future__ import annotations
import json
from urllib.request import Request,urlopen

BASE="https://api.exchange.coinbase.com"
PRODUCTS_URL=BASE+"/products"
READ_ONLY=True
EXECUTION_AUTHORITY=False

def _get_json(url,timeout_seconds):
    req=Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0 read-only","Accept":"application/json"})
    with urlopen(req,timeout=timeout_seconds) as r:
        return json.loads(r.read().decode("utf-8"))

def discover_coinbase_public_products(timeout_seconds=20.0,quote_currencies=("USD","USDC"),limit=1000):
    rows=_get_json(PRODUCTS_URL,timeout_seconds)
    out=[]
    allowed=set(quote_currencies)
    for row in rows if isinstance(rows,list) else ():
        pid=str(row.get("id") or "")
        if not pid: continue
        if allowed and str(row.get("quote_currency") or "") not in allowed: continue
        if row.get("trading_disabled") is True: continue
        out.append({
            "product_id":pid,
            "base_currency":row.get("base_currency"),
            "quote_currency":row.get("quote_currency"),
            "base_increment":row.get("base_increment"),
            "quote_increment":row.get("quote_increment"),
            "min_market_funds":row.get("min_market_funds"),
            "status":row.get("status"),
            "cancel_only":row.get("cancel_only"),
            "limit_only":row.get("limit_only"),
            "post_only":row.get("post_only"),
            "source_url":PRODUCTS_URL,
        })
        if len(out)>=int(limit): break
    return tuple(out)
