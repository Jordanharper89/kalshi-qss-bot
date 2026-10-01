from __future__ import annotations
import asyncio,json,os,time,urllib.request
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161k_phase8_universal_live_economics_producer_rebuild import decode_live_trade

FREEZE="runtime_state/solana_opportunities/solana_scanner/phase8_strict_live_prospective_freezes.json"
WS=os.environ.get("SOLANA_WS_URL","wss://api.mainnet-beta.solana.com")
RPC=os.environ.get("SOLANA_RPC_URL","https://api.mainnet.solana.com")

def rpc(sig,retries=6):
 payload=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[sig,
  {"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":0}]}).encode()
 last=None
 for n in range(retries):
  try:
   req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json","User-Agent":"qseries-usls161o2"})
   with urllib.request.urlopen(req,timeout=20) as r:return json.loads(r.read()).get("result")
  except Exception as e:
   last=e;time.sleep(min(1.5*(n+1),6))
 return None

async def follow(markets,seconds=75,max_sigs=80):
 import websockets
 rows=[];acks={};seen=set()
 async with websockets.connect(WS,ping_interval=20,ping_timeout=20,close_timeout=3,max_size=12_000_000) as ws:
  for i,m in enumerate(markets,1):
   req={"jsonrpc":"2.0","id":i,"method":"logsSubscribe",
        "params":[{"mentions":[m["market_address"]]},{"commitment":"confirmed"}]}
   await ws.send(json.dumps(req))
  deadline=time.time()+seconds
  while time.time()<deadline and len(rows)<max_sigs:
   try:msg=json.loads(await asyncio.wait_for(ws.recv(),timeout=max(.2,deadline-time.time())))
   except asyncio.TimeoutError:break
   if "id" in msg and "result" in msg:
    acks[int(msg["id"])]=msg["result"];continue
   if msg.get("method")!="logsNotification":continue
   params=msg.get("params") or {};sub=params.get("subscription")
   req_id=next((rid for rid,sid in acks.items() if sid==sub),None)
   if req_id is None or req_id<1 or req_id>len(markets):continue
   target=markets[req_id-1]
   res=params.get("result") or {};v=res.get("value") or {}
   sig=v.get("signature")
   if not sig or sig in seen or v.get("err") is not None:continue
   seen.add(sig)
   rows.append({"family":target["family"],"market_address":target["market_address"],
                "signature":sig,"slot":(res.get("context") or {}).get("slot"),
                "observed_unix":time.time()})
 return rows

def _friction(root):
 out={}
 for p in (Path(root)/"runtime_state/solana_opportunities").rglob("*.json"):
  try:d=json.loads(p.read_text(encoding="utf-8",errors="ignore"))
  except Exception:continue
  rows=d.get("ready_rows") if isinstance(d,dict) else None
  if not isinstance(rows,list):rows=d.get("rows") if isinstance(d,dict) else None
  if not isinstance(rows,list):continue
  for r in rows:
   if not isinstance(r,dict):continue
   fam=str(r.get("family") or r.get("venue") or "").upper()
   fee=r.get("fee_fraction");dev=r.get("realized_execution_deviation_fraction")
   if isinstance(fee,(int,float)) and isinstance(dev,(int,float)):
    z=out.setdefault(fam,{"fee":[],"dev":[]})
    z["fee"].append(float(fee));z["dev"].append(abs(float(dev)))
 def med(v):
  v=sorted(v);return None if not v else v[len(v)//2]
 return {f:{"n":len(v["fee"]),"fee":med(v["fee"]),"dev":med(v["dev"])} for f,v in out.items()}

def run(root,seconds=75,max_sigs=80):
 root=Path(root);f=json.loads((root/FREEZE).read_text(encoding="utf-8"))
 setups=f.get("frozen_setups") or []
 unique=[];seen=set()
 for s in setups:
  k=(s["family"],str(s["market_address"]))
  if k not in seen:
   seen.add(k);unique.append({"family":s["family"],"market_address":str(s["market_address"])})
 hits=asyncio.run(follow(unique,seconds=seconds,max_sigs=max_sigs))
 decoded=[];hydrated=0
 for h in hits:
  tx=rpc(h["signature"])
  if not isinstance(tx,dict):continue
  hydrated+=1
  for z in decode_live_trade(h["family"],h["signature"],tx,h["observed_unix"]):
   if z.get("market_address") is None:continue
   if str(z["market_address"])!=h["market_address"]:continue
   if z.get("trade_signature")!=h["signature"] or not z.get("strict_live_provenance"):continue
   decoded.append(z)
 by={}
 for z in decoded:
  k=(z["family"],str(z["market_address"]),z["input_asset"],z["output_asset"])
  by.setdefault(k,[]).append(z)
 cases=[]
 for s in setups:
  k=(s["family"],str(s["market_address"]),s["input_asset"],s["output_asset"])
  xs=[x for x in by.get(k,[]) if x["observed_unix"]>s["freeze_unix"]]
  if not xs:continue
  x=min(xs,key=lambda q:q["observed_unix"])
  p0=float(s["last_price"]);p1=float(x["effective_output_per_input"])
  cases.append({"freeze_hash":s["freeze_hash"],"family":s["family"],"market_address":s["market_address"],
   "input_asset":s["input_asset"],"output_asset":s["output_asset"],
   "freeze_unix":s["freeze_unix"],"later_observed_unix":x["observed_unix"],
   "later_trade_signature":x["trade_signature"],"entry_reference_price":p0,"later_price":p1,
   "gross_forward_return":p1/p0-1 if p0 else None,"execution_authority":False})
 fr=_friction(root);net=[]
 for c in cases:
  q=fr.get(c["family"]);g=c["gross_forward_return"]
  if q and q["fee"] is not None and q["dev"] is not None and isinstance(g,(int,float)):
   cost=2*q["fee"]+2*q["dev"];net.append({**c,"modeled_round_trip_friction":cost,"net_forward_return":g-cost})
 gv=[c["gross_forward_return"] for c in cases if isinstance(c.get("gross_forward_return"),(int,float))]
 nv=[c["net_forward_return"] for c in net]
 decision=("NO_PROSPECTIVE_CASES" if not gv else "INSUFFICIENT_NET_FRICTION_SAMPLE" if len(nv)<5 else
  "POSITIVE_NET_EXPECTANCY_OBSERVED_NOT_YET_CERTIFIED" if sum(nv)/len(nv)>0 else "NO_POSITIVE_NET_EXPECTANCY_OBSERVED")
 return {"revision":"USLS_161O2","frozen_market_count":len(unique),"frozen_setup_count":len(setups),
  "market_subscription_hit_count":len(hits),"hydrated_transaction_count":hydrated,
  "strict_same_market_decoded_count":len(decoded),"prospective_case_count":len(cases),
  "prospective_families":sorted({c["family"] for c in cases}),
  "mean_gross_forward_return":None if not gv else sum(gv)/len(gv),
  "gross_positive_frequency":None if not gv else sum(v>0 for v in gv)/len(gv),
  "net_case_count":len(net),"net_friction_families":sorted({c["family"] for c in net}),
  "mean_net_forward_return":None if not nv else sum(nv)/len(nv),
  "net_positive_frequency":None if not nv else sum(v>0 for v in nv)/len(nv),
  "profitability_decision":decision,"cases":cases,"net_cases":net,
  "sampling_policy":"SUBSCRIBE_TO_EXACT_FROZEN_MARKETS_NOT_RANDOM_UNIVERSAL_RECENSUS",
  "next_boundary":"ACCUMULATE_PROSPECTIVE_OOS_AND_EXPAND_PENDING_FAMILIES",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_exact_frozen_market_outcomes.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
