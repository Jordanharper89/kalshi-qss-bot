from __future__ import annotations
import asyncio,json,os,time,urllib.request
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161z_phase8_damm_v1_live_decoder_extension import decode_live_trade_extended,SUPPORTED
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_045b_universal_multidex_decoder_framework import PROGRAMS
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_075_meteora_damm_v1_program_correction import CORRECT_PROGRAM
CHK="runtime_state/solana_opportunities/solana_scanner/phase8_updated_learning_coverage_checkpoint.json"
WS=os.environ.get("SOLANA_WS_URL","wss://api.mainnet-beta.solana.com")
RPC=os.environ.get("SOLANA_RPC_URL","https://api.mainnet.solana.com")
MAP={**{k:v for k,v in PROGRAMS.items() if k!="METEORA_DYN"},"METEORA_DAMM_V2":PROGRAMS["METEORA_DAMM"],"METEORA_DAMM_V1":CORRECT_PROGRAM}
def rpc(sig,retries=5):
 payload=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[sig,{"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":0}]}).encode()
 for n in range(retries):
  try:
   req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json","User-Agent":"qseries-usls162a"})
   with urllib.request.urlopen(req,timeout=20) as r:return json.loads(r.read()).get("result")
  except Exception:time.sleep(min(1.5*(n+1),6))
 return None
def targets(root):
 p=Path(root)/CHK
 rows=json.loads(p.read_text(encoding="utf-8")).get("rows",[]) if p.exists() else []
 wanted=[x["family"] for x in rows if not x.get("ready") and x["family"] in SUPPORTED and x["family"] in MAP]
 return wanted or [f for f in SUPPORTED if f in MAP]
async def cap(families,seconds=85,per_family=10):
 import websockets
 pairs=[(f,MAP[f]) for f in families];acks={};byid={i+1:f for i,(f,p) in enumerate(pairs)}
 seen=set();rows=[];counts={f:0 for f in families}
 async with websockets.connect(WS,ping_interval=20,ping_timeout=20,close_timeout=3,max_size=12_000_000) as ws:
  for i,(f,pid) in enumerate(pairs,1):
   await ws.send(json.dumps({"jsonrpc":"2.0","id":i,"method":"logsSubscribe","params":[{"mentions":[pid]},{"commitment":"confirmed"}]}))
  deadline=time.time()+seconds
  while time.time()<deadline:
   try:m=json.loads(await asyncio.wait_for(ws.recv(),timeout=max(.2,deadline-time.time())))
   except asyncio.TimeoutError:break
   if "id" in m and "result" in m:acks[int(m["id"])]=m["result"];continue
   if m.get("method")!="logsNotification":continue
   sub=(m.get("params") or {}).get("subscription");rid=next((i for i,s in acks.items() if s==sub),None);fam=byid.get(rid)
   if not fam or counts[fam]>=per_family:continue
   res=((m.get("params") or {}).get("result") or {});v=res.get("value") or {};sig=v.get("signature")
   if not sig or (fam,sig) in seen or v.get("err") is not None:continue
   seen.add((fam,sig));counts[fam]+=1;rows.append({"family":fam,"signature":sig,"observed_unix":time.time()})
 return rows
def run(root):
 fams=targets(root);hits=asyncio.run(cap(fams));out=[];hydrated=0
 for h in hits:
  tx=rpc(h["signature"])
  if not isinstance(tx,dict):continue
  hydrated+=1;out+=decode_live_trade_extended(h["family"],h["signature"],tx,h["observed_unix"])
 by={}
 for x in out:
  z=by.setdefault(x["family"],{"rows":0,"markets":set()});z["rows"]+=1;z["markets"].add(str(x["market_address"]))
 support={f:{"rows":v["rows"],"market_count":len(v["markets"])} for f,v in by.items()}
 return {"revision":"USLS_162A","target_families":fams,"signature_count":len(hits),"hydrated_transaction_count":hydrated,
  "strict_live_economic_row_count":len(out),"family_support":support,"rows":out,
  "next_boundary":"FREEZE_NEW_GAP_TARGETED_COHORT","profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_gap_targeted_live_economics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
