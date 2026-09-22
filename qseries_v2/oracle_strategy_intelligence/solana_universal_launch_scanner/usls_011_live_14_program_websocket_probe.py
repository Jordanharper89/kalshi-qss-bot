from __future__ import annotations
import asyncio,json,time
from pathlib import Path
WS="wss://api.mainnet-beta.solana.com"
async def probe(root,seconds=12):
 import websockets
 root=Path(root)
 man=json.loads((root/"runtime_state/solana_opportunities/universal_launch_scanner/subscription_manifest.json").read_text(encoding="utf-8"))
 subs=man["subscriptions"];reqs=[];id_to_family={}
 for i,x in enumerate(subs,1):
  reqs.append({"jsonrpc":"2.0","id":i,"method":"logsSubscribe","params":[{"mentions":[x["program_id"]]},{"commitment":"confirmed"}]})
  id_to_family[i]=x["family"]
 acks={};sub_to_family={};notifications=[];started=time.time()
 async with websockets.connect(WS,ping_interval=20,ping_timeout=20,close_timeout=3,max_size=8_000_000) as ws:
  for r in reqs: await ws.send(json.dumps(r))
  deadline=time.time()+seconds
  while time.time()<deadline:
   try: msg=json.loads(await asyncio.wait_for(ws.recv(),timeout=max(.2,deadline-time.time())))
   except asyncio.TimeoutError: break
   if "id" in msg and "result" in msg:
    acks[msg["id"]]=msg["result"];sub_to_family[msg["result"]]=id_to_family.get(msg["id"])
   elif msg.get("method")=="logsNotification":
    p=msg.get("params") or {};res=p.get("result") or {};val=res.get("value") or {}
    notifications.append({"family":sub_to_family.get(p.get("subscription"),"UNKNOWN_PROGRAM"),"subscription":p.get("subscription"),
     "signature":val.get("signature"),"slot":((res.get("context") or {}).get("slot")),"observed_unix":time.time(),
     "err":val.get("err"),"logs":val.get("logs") or []})
 counts={}
 for x in notifications: counts[x["family"]]=counts.get(x["family"],0)+1
 return {"revision":"USLS_011","ack_count":len(acks),"expected_ack_count":len(reqs),"notification_count":len(notifications),
  "family_notification_counts":counts,"notifications":notifications[-500:],"probe_seconds":time.time()-started,
  "execution_authority":False,"read_only":True}
def run(root,seconds=12):
 d=asyncio.run(probe(root,seconds))
 p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/live_14_program_probe.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
