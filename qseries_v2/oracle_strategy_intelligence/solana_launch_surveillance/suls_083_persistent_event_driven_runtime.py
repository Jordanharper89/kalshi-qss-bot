from __future__ import annotations
import asyncio,json,time
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_076_birth_log_notification_filter import is_birth
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_080_event_driven_lifecycle_bridge import run as bridge

def _hydrate(sig,slot,received):
 tx=_rpc("getTransaction",[sig,{"commitment":"confirmed","encoding":"jsonParsed",
   "maxSupportedTransactionVersion":1}],20.0)
 if not tx or ((tx.get("meta") or {}).get("err") is not None):return None
 bt=tx.get("blockTime")
 return {"signature":sig,"slot":int(tx.get("slot") or slot or 0),"block_time":bt,
  "observed_unix":float(received),"hydrated_unix":time.time(),
  "age_seconds":None if bt is None else max(0.0,float(received)-float(bt)),
  "envelope":{"signature":sig,"slot":tx.get("slot"),"block_time":bt,"raw_transaction":tx},
  "state":"CONFIRMED_EVENT_DRIVEN_BIRTH","trigger_commitment":"confirmed",
  "transport":"logsSubscribe","recovered_after_gap":False,"execution_authority":False}

def _append_birth(root,row):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/event_driven_birth_inbox.json"
 old=json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"births":[]}
 rows=list(old.get("births") or []);seen={x.get("signature") for x in rows}
 if row and row["signature"] not in seen:rows.append(row)
 out={"revision":"SULS_083","birth_count":len(rows),"births":rows,"execution_authority":False,"read_only":True}
 p.write_text(json.dumps(out,indent=2,sort_keys=True,default=str),encoding="utf-8")

async def serve(root,max_notifications=None,max_seconds=None):
 import websockets
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 c=json.loads((base/"confirmed_logs_subscription_contract.json").read_text(encoding="utf-8"))
 stop=root/"runtime_state/solana_intelligence/STOP_OSI_LIVE"
 cp=base/"persistent_event_driven_runtime_status.json"
 seen=set();notes=0;births=0;started=time.time()
 async with websockets.connect(c["ws_url"],ping_interval=20,ping_timeout=20,close_timeout=3,max_size=8_000_000) as ws:
  for sub in c["subscriptions"]:await ws.send(json.dumps(sub))
  acks=0
  while not stop.exists():
   if max_notifications is not None and notes>=int(max_notifications):break
   if max_seconds is not None and time.time()-started>=float(max_seconds):break
   try:raw=await asyncio.wait_for(ws.recv(),timeout=1.0)
   except asyncio.TimeoutError:
    continue
   msg=json.loads(raw)
   if "id" in msg and "result" in msg:
    acks+=1;continue
   if msg.get("method")!="logsNotification":continue
   notes+=1;received=time.time()
   result=((msg.get("params") or {}).get("result") or {})
   v=result.get("value") or {};ctx=result.get("context") or {}
   sig=v.get("signature");logs=v.get("logs") or []
   if v.get("err") is None and sig and sig not in seen and is_birth(logs):
    seen.add(sig);row=_hydrate(sig,ctx.get("slot"),received)
    if row:
     _append_birth(root,row);bridge(root);births+=1
   cp.write_text(json.dumps({"revision":"SULS_083","connected":True,"ack_count":acks,
    "notifications":notes,"births_hydrated":births,"started_unix":started,"heartbeat_unix":time.time(),
    "execution_authority":False,"read_only":True},indent=2,sort_keys=True),encoding="utf-8")
 return {"ack_count":acks,"notifications":notes,"births_hydrated":births}

def run_forever(root):
 backoff=1.0
 while True:
  try:
   asyncio.run(serve(root));backoff=1.0
   if (root/"runtime_state/solana_intelligence/STOP_OSI_LIVE").exists():return
  except KeyboardInterrupt:raise
  except Exception:
   time.sleep(backoff);backoff=min(30.0,backoff*2.0)
