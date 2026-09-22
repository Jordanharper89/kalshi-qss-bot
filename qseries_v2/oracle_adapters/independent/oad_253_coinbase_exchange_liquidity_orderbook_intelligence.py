import json, urllib.request
from .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
BASE="https://api.exchange.coinbase.com"
def _get(url,timeout=15.0):
 req=urllib.request.Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=float(timeout)) as r: return json.loads(r.read().decode())
def acquire_coinbase_orderbook(product_id="BTC-USD",level=2,timeout=15.0,fetch=_get):
 p=str(product_id).upper()
 if level not in (1,2): raise ValueError("public read-only levels 1 or 2 only")
 d=fetch(f"{BASE}/products/{p}/book?level={level}",timeout)
 bids=d.get("bids") or []; asks=d.get("asks") or []
 if not bids or not asks: raise RuntimeError("Coinbase order book empty")
 bp=float(bids[0][0]); ap=float(asks[0][0])
 payload={"product_id":p,"sequence":d.get("sequence"),"best_bid":bp,"best_ask":ap,"spread":ap-bp,"bid_levels":len(bids),"ask_levels":len(asks),"level":level}
 return build_independent_crypto_observation(source_id="source.exchange.coinbase.orderbook."+p.lower(),provider="coinbase_exchange",source_class="exchange_liquidity",subject=p,observation_type="l2_orderbook",payload=payload)
