import json, urllib.parse, urllib.request
from .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
BASE="https://api.bybit.com/v5/market/tickers"
def _get(url,timeout=15.0):
 req=urllib.request.Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=float(timeout)) as r: return json.loads(r.read().decode())
def acquire_derivatives_state(symbol="BTCUSDT",timeout=15.0,fetch=_get):
 s=str(symbol).upper()
 d=fetch(BASE+"?"+urllib.parse.urlencode({"category":"linear","symbol":s}),timeout)
 if int(d.get("retCode",-1))!=0: raise RuntimeError("derivatives provider rejected request")
 rows=((d.get("result") or {}).get("list") or [])
 if not rows: raise RuntimeError("derivatives ticker unavailable")
 x=rows[0]
 payload={"symbol":s,"last_price":x.get("lastPrice"),"mark_price":x.get("markPrice"),"index_price":x.get("indexPrice"),"open_interest":x.get("openInterest"),"open_interest_value":x.get("openInterestValue"),"funding_rate":x.get("fundingRate"),"next_funding_time":x.get("nextFundingTime"),"volume_24h":x.get("volume24h"),"turnover_24h":x.get("turnover24h")}
 return build_independent_crypto_observation(source_id="source.derivatives.bybit."+s.lower(),provider="bybit_public_market",source_class="derivatives_state",subject=s,observation_type="open_interest_funding",payload=payload)
