from __future__ import annotations
import asyncio,json,time
from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_076_birth_log_notification_filter import is_birth

def _load_contract(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/confirmed_logs_subscription_contract.json"
 return json.loads(p.read_text(encoding="utf-8"))

def _hydrate(sig,slot,received_unix):
 tx=_rpc("getTransaction",[sig,{"commitment":"confirmed","encoding":"jsonParsed",
   "maxSupportedTransactionVersion":1}],20.0)
 if not tx:return None
 meta=tx.get("meta") or {}
 if meta.get("err") is not None:return None
 bt=tx.get("blockTime")
 return {"signature":sig,"slot":int(tx.get("slot") or slot or 0),"block_time":bt,
  "observed_unix":float(received_unix),"hydrated_unix":time.time(),
  "age_seconds":None if bt is None else max(0.0,float(received_unix)-float(bt)),
  "envelope":{"signature":sig,"slot":tx.get("slot"),"block_time":bt,"raw_transaction":tx},
  "state":"CONFIRMED_EVENT_DRIVEN_BIRTH","trigger_commitment":"confirmed",
  "transport":"logsSubscribe","recovered_after_gap":False,"execution_authority":False}

async def probe(root,max_notifications=20,timeout_seconds=12.0):
 import websockets
 c=_load_contract(root);acks=[];seen=set();births=[];notes=0;t0=time.time()
 async with websockets.connect(c["ws_url"],ping_interval=20,ping_timeout=20,close_timeout=3,max_size=8_000_000) as ws:
  for sub in c["subscriptions"]:await ws.send(json.dumps(sub))
  deadline=time.monotonic()+float(timeout_seconds)
  while time.monotonic()<deadline and notes<int(max_notifications):
   try:raw=await asyncio.wait_for(ws.recv(),timeout=max(0.1,deadline-time.monotonic()))
   except asyncio.TimeoutError:break
   msg=json.loads(raw)
   if "id" in msg and "result" in msg:
    acks.append({"id":msg["id"],"subscription":msg["result"]});continue
   if msg.get("method")!="logsNotification":continue
   notes+=1;received=time.time()
   result=((msg.get("params") or {}).get("result") or {})
   v=result.get("value") or {};ctx=result.get("context") or {}
   sig=v.get("signature");logs=v.get("logs") or []
   if v.get("err") is not None or not sig or sig in seen or not is_birth(logs):continue
   seen.add(sig)
   row=_hydrate(sig,ctx.get("slot"),received)
   if row:births.append(row)
 return {"revision":"SULS_079","connected":True,"ack_count":len(acks),"notifications_examined":notes,
  "births_hydrated":len(births),"births":births,"elapsed_seconds":time.time()-t0,
  "execution_authority":False,"read_only":True}

def run(root):
 d=asyncio.run(probe(root))
 p=root/"runtime_state/solana_opportunities/launch_surveillance/event_driven_birth_inbox.json"
 old=json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"births":[]}
 rows=list(old.get("births") or []);seen={x.get("signature") for x in rows}
 for x in d["births"]:
  if x["signature"] not in seen:rows.append(x);seen.add(x["signature"])
 out=dict(d);out["births"]=rows;out["birth_count"]=len(rows)
 p.write_text(json.dumps(out,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,out
