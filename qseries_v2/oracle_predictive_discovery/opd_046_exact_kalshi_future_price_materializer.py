from datetime import datetime,timezone
SOURCE="source.kalshi.market_data"
execution_authority=False
def event_epoch(msg,outer_epoch):
 if msg.get("ts") is not None:
  try:return float(msg["ts"])
  except:pass
 if msg.get("ts_ms") is not None:
  try:return float(msg["ts_ms"])/1000.0
  except:pass
 if msg.get("time"):
  try:
   d=datetime.fromisoformat(str(msg["time"]).replace("Z","+00:00"))
   if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
   return d.timestamp()
  except:pass
 return float(outer_epoch)
def price(msg):
 for k in ("yes_price_dollars","price_dollars","last_price_dollars"):
  if msg.get(k) is not None:
   try:return float(msg[k])
   except:pass
 try:
  b=float(msg["yes_bid_dollars"]);a=float(msg["yes_ask_dollars"]);return (b+a)/2.0
 except:return None
def canonical_point(obj,outer_epoch):
 if not isinstance(obj,dict):return None
 p=obj.get("payload");m=p.get("message") if isinstance(p,dict) else None
 if not isinstance(m,dict):return None
 ticker=str(m.get("market_ticker") or p.get("source_market_id") or "")
 px=price(m)
 if not ticker.startswith("KX") or px is None or not 0<=px<=1:return None
 return {"ticker":ticker,"event_epoch":event_epoch(m,outer_epoch),"price":px}
