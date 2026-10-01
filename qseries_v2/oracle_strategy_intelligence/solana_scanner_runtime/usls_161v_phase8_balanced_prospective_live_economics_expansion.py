from __future__ import annotations
import asyncio,json,os,time,urllib.request
from collections import defaultdict
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161k_phase8_universal_live_economics_producer_rebuild import decode_live_trade,SUPPORTED
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_045b_universal_multidex_decoder_framework import PROGRAMS

WS=os.environ.get("SOLANA_WS_URL","wss://api.mainnet-beta.solana.com")
RPC=os.environ.get("SOLANA_RPC_URL","https://api.mainnet.solana.com")
ALIASES={"METEORA_DAMM":"METEORA_DAMM_V2"}

def _rpc(sig,retries=5):
 payload=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[sig,
  {"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":0}]}).encode()
 for n in range(retries):
  try:
   req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json","User-Agent":"qseries-usls161v"})
   with urllib.request.urlopen(req,timeout=20) as r:return json.loads(r.read()).get("result")
  except Exception:time.sleep(min(1.5*(n+1),6))
 return None

async def capture(seconds=70,per_family=8):
 import websockets
 targets=[(ALIASES.get(f,f),pid) for f,pid in PROGRAMS.items() if ALIASES.get(f,f) in SUPPORTED]
 byid={i+1:f for i,(f,p) in enumerate(targets)}
 rows=[];acks={};counts=defaultdict(int);seen=set()
 async with websockets.connect(WS,ping_interval=20,ping_timeout=20,close_timeout=3,max_size=12_000_000) as ws:
  for i,(fam,pid) in enumerate(targets,1):
   await ws.send(json.dumps({"jsonrpc":"2.0","id":i,"method":"logsSubscribe",
    "params":[{"mentions":[pid]},{"commitment":"confirmed"}]}))
  deadline=time.time()+seconds
  while time.time()<deadline:
   try:m=json.loads(await asyncio.wait_for(ws.recv(),timeout=max(.2,deadline-time.time())))
   except asyncio.TimeoutError:break
   if "id" in m and "result" in m:acks[int(m["id"])]=m["result"];continue
   if m.get("method")!="logsNotification":continue
   params=m.get("params") or {};sub=params.get("subscription");rid=next((i for i,s in acks.items() if s==sub),None)
   fam=byid.get(rid)
   if not fam or counts[fam]>=per_family:continue
   res=params.get("result") or {};v=res.get("value") or {};sig=v.get("signature")
   if not sig or (fam,sig) in seen or v.get("err") is not None:continue
   seen.add((fam,sig));counts[fam]+=1
   rows.append({"family":fam,"signature":sig,"slot":(res.get("context") or {}).get("slot"),"observed_unix":time.time()})
 return rows

def run(root,seconds=70,per_family=8):
 hits=asyncio.run(capture(seconds,per_family));decoded=[];hydrated=0
 for h in hits:
  tx=_rpc(h["signature"])
  if not isinstance(tx,dict):continue
  hydrated+=1
  for z in decode_live_trade(h["family"],h["signature"],tx,h["observed_unix"]):
   if z.get("trade_signature")==h["signature"] and z.get("strict_live_provenance") and z.get("market_address"):
    decoded.append(z)
 by={}
 for z in decoded:
  q=by.setdefault(z["family"],{"rows":0,"markets":set()});q["rows"]+=1;q["markets"].add(str(z["market_address"]))
 support={f:{"rows":v["rows"],"market_count":len(v["markets"])} for f,v in by.items()}
 return {"revision":"USLS_161V","capture_seconds":seconds,"per_family_cap":per_family,
  "prospective_signature_count":len(hits),"hydrated_transaction_count":hydrated,
  "strict_live_economic_row_count":len(decoded),"family_support":support,"rows":decoded,
  "rpc_source":"configured" if os.environ.get("SOLANA_RPC_URL") else "public_fallback",
  "sampling_policy":"BALANCED_PER_FAMILY_PROGRAM_SUBSCRIPTIONS_NO_GLOBAL_FIRST24_BIAS",
  "next_boundary":"EXTEND_PROSPECTIVE_FREEZE_LEDGER",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_balanced_live_economics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
