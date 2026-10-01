from __future__ import annotations
import asyncio,json,os,time,urllib.request
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161k_phase8_universal_live_economics_producer_rebuild import decode_live_trade,SUPPORTED
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router import capture

RPC=os.environ.get("SOLANA_RPC_URL","https://api.mainnet.solana.com")
def rpc(sig,retries=5):
 payload=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[sig,
  {"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":0}]}).encode()
 last=None
 for n in range(retries):
  try:
   req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json","User-Agent":"qseries-usls161m"})
   with urllib.request.urlopen(req,timeout=20) as r:return json.loads(r.read()).get("result")
  except Exception as e:last=e;time.sleep(min(1.5*(n+1),6))
 return None

def run(root,seconds=15,max_rows=12000,max_sigs=24):
 cap=asyncio.run(capture(seconds=seconds,max_rows=max_rows));seen=set();targets=[]
 for x in cap.get("rows",[]):
  fam=str(x.get("venue") or "").upper()
  if fam=="METEORA_DAMM":fam="METEORA_DAMM_V2"
  sig=x.get("signature")
  if fam in SUPPORTED and sig and sig not in seen:
   seen.add(sig);targets.append((fam,sig,x.get("observed_unix")))
  if len(targets)>=max_sigs:break
 out=[];hydrated=0
 for fam,sig,obs in targets:
  tx=rpc(sig)
  if not isinstance(tx,dict):continue
  hydrated+=1
  for z in decode_live_trade(fam,sig,tx,obs):
   if z.get("trade_signature")==sig and z.get("strict_live_provenance") and z.get("market_address"):
    out.append(z)
 by={}
 for z in out:
  q=by.setdefault(z["family"],{"rows":0,"markets":set()});q["rows"]+=1;q["markets"].add(str(z["market_address"]))
 support={f:{"rows":v["rows"],"market_count":len(v["markets"])} for f,v in by.items()}
 return {"revision":"USLS_161M","router_row_count":cap.get("row_count",0),"target_signature_count":len(targets),
  "hydrated_transaction_count":hydrated,"strict_live_economic_row_count":len(out),"family_support":support,"rows":out,
  "rpc_source":"configured" if os.environ.get("SOLANA_RPC_URL") else "public_fallback",
  "next_boundary":"PROSPECTIVE_FEATURE_FREEZE_FROM_STRICT_LIVE_ECONOMICS",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_strict_live_direct_economics.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
