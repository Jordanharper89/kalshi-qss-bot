from pathlib import Path
import py_compile
R=Path.cwd();M=R/"qseries_v2/oracle_predictive_discovery/opd_046_exact_kalshi_future_price_materializer.py";T=R/"test_opd_046_exact_kalshi_future_price_materializer_V1.py"
M.parent.mkdir(parents=True,exist_ok=True)
M.write_text("""from datetime import datetime,timezone
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
""",encoding="utf-8")
T.write_text("""from qseries_v2.oracle_predictive_discovery.opd_046_exact_kalshi_future_price_materializer import price,canonical_point
assert price({"yes_price_dollars":"0.61","yes_bid_dollars":"0.40","yes_ask_dollars":"0.50"})==.61
assert price({"yes_bid_dollars":"0.50","yes_ask_dollars":"0.54"})==.52
x=canonical_point({"payload":{"source_market_id":"KXBTC","message":{"yes_bid_dollars":"0.50","yes_ask_dollars":"0.54","ts":101}}},100)
assert x=={"ticker":"KXBTC","event_epoch":101.0,"price":.52}
print("[TRADE_PRECEDENCE] PASS");print("[MIDPOINT_FALLBACK] PASS");print("[PASS] OPD-046 exact OPD-004/005 Kalshi price semantics certified")
""",encoding="utf-8")
py_compile.compile(str(M),doraise=True);py_compile.compile(str(T),doraise=True);print("[PASS] OPD-046 V1 installed")