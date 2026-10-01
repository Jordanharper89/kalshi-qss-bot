from __future__ import annotations
import asyncio,json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_022_live_pump_create_v2_capture import _tx
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162j_phase8_universal_14_family_live_decoder_closure import decode_live_trade_all14

WS="wss://api.mainnet-beta.solana.com"
PROGRAMS={"PUMP_FUN":"6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
"PUMP_SWAP":"pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"}

async def capture(seconds=90,per_family=28):
 import websockets
 pairs=list(PROGRAMS.items());acks={};byid={i+1:f for i,(f,p) in enumerate(pairs)}
 counts={f:0 for f in PROGRAMS};seen=set();hits=[]
 async with websockets.connect(WS,ping_interval=20,ping_timeout=20,close_timeout=3,max_size=12_000_000) as ws:
  for i,(fam,pid) in enumerate(pairs,1):
   await ws.send(json.dumps({"jsonrpc":"2.0","id":i,"method":"logsSubscribe",
    "params":[{"mentions":[pid]},{"commitment":"confirmed"}]}))
  deadline=time.time()+seconds
  while time.time()<deadline:
   try:m=json.loads(await asyncio.wait_for(ws.recv(),timeout=max(.2,deadline-time.time())))
   except asyncio.TimeoutError:break
   if "id" in m and "result" in m:
    acks[int(m["id"])]=m["result"];continue
   if m.get("method")!="logsNotification":continue
   sub=(m.get("params") or {}).get("subscription");rid=next((i for i,s in acks.items() if s==sub),None);fam=byid.get(rid)
   if not fam or counts[fam]>=per_family:continue
   res=((m.get("params") or {}).get("result") or {});v=res.get("value") or {};sig=v.get("signature")
   if not sig or (fam,sig) in seen or v.get("err") is not None:continue
   seen.add((fam,sig));counts[fam]+=1;hits.append({"family":fam,"signature":sig,"observed_unix":time.time()})
 return hits

def run(root):
 hits=asyncio.run(capture());rows=[];hydrated=0
 for h in hits:
  tx=_tx(h["signature"])
  if not tx:continue
  hydrated+=1
  rows+=decode_live_trade_all14(root,h["family"],h["signature"],tx,h["observed_unix"])
 fam={}
 for x in rows:
  z=fam.setdefault(x["family"],{"rows":0,"markets":set()});z["rows"]+=1;z["markets"].add(str(x["market_address"]))
 support={f:{"rows":z["rows"],"market_count":len(z["markets"])} for f,z in fam.items()}
 return {"revision":"USLS_162K","signature_count":len(hits),"hydrated_transaction_count":hydrated,
  "strict_live_economic_row_count":len(rows),"family_support":support,"rows":rows,
  "target_families":["PUMP_FUN","PUMP_SWAP"],
  "purpose":"PUMP_FUN_UNIVERSAL_COVERAGE_PLUS_PUMPSWAP_PHASE7_FRICTION_INTERSECTION",
  "next_boundary":"FREEZE_PUMP_FUN_AND_PUMPSWAP_TARGETED_COHORTS",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_pump_targeted_live_economics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
