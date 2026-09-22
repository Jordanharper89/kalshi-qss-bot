from __future__ import annotations
import asyncio,json,time

async def probe(root,max_messages=6,timeout_seconds=12.0):
 import websockets
 c=json.loads((root/"runtime_state/solana_opportunities/launch_surveillance/confirmed_logs_subscription_contract.json").read_text(encoding="utf-8"))
 ws_url=c["ws_url"];acks=[];notes=[];t0=time.time()
 async with websockets.connect(ws_url,ping_interval=20,ping_timeout=20,close_timeout=3,max_size=8_000_000) as ws:
  for sub in c["subscriptions"]:
   await ws.send(json.dumps(sub))
  deadline=time.monotonic()+float(timeout_seconds)
  while time.monotonic()<deadline and len(notes)<int(max_messages):
   remain=max(0.1,deadline-time.monotonic())
   try:raw=await asyncio.wait_for(ws.recv(),timeout=remain)
   except asyncio.TimeoutError:break
   msg=json.loads(raw)
   if "id" in msg and "result" in msg:
    acks.append({"id":msg["id"],"subscription":msg["result"]});continue
   if msg.get("method")=="logsNotification":
    v=(((msg.get("params") or {}).get("result") or {}).get("value") or {})
    ctx=(((msg.get("params") or {}).get("result") or {}).get("context") or {})
    notes.append({"slot":ctx.get("slot"),"signature":v.get("signature"),"err":v.get("err"),
      "logs":v.get("logs") or [],"received_unix":time.time()})
 return {"revision":"SULS_075","connected":True,"ack_count":len(acks),"notification_count":len(notes),
  "acks":acks,"notifications":notes,"elapsed_seconds":time.time()-t0,
  "execution_authority":False,"read_only":True}

def run(root):
 d=asyncio.run(probe(root))
 p=root/"runtime_state/solana_opportunities/launch_surveillance/physical_confirmed_logs_subscription_probe.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
