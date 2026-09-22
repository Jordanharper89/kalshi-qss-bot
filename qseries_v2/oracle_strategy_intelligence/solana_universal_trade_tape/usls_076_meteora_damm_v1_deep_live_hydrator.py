from __future__ import annotations
import json,os,time,urllib.request
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_075_meteora_damm_v1_program_correction import CORRECT_PROGRAM
RPC=os.environ.get("SOLANA_RPC_URL","https://api.mainnet.solana.com")

def rpc(method,params,retries=6):
 payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
 for n in range(retries):
  try:
   req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json","User-Agent":"qseries-usls076"})
   with urllib.request.urlopen(req,timeout=20) as r:return json.loads(r.read()).get("result")
  except Exception:time.sleep(min(1.5*(n+1),6))
 return None

def signatures(limit=120):
 out=[];before=None
 while len(out)<limit:
  opts={"limit":min(100,limit-len(out)),"commitment":"confirmed"}
  if before:opts["before"]=before
  page=rpc("getSignaturesForAddress",[CORRECT_PROGRAM,opts]) or []
  out += [x["signature"] for x in page if x.get("signature") and x.get("err") is None]
  if not page or len(page)<opts["limit"]:break
  before=page[-1].get("signature");time.sleep(.35)
 return out

def hydrate(sig):
 return rpc("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":0}])

def build(root):
 sigs=signatures();rows=[]
 for i,s in enumerate(sigs):
  t=hydrate(s);rows.append({"signature":s,"transaction":t,"hydrated":t is not None,"execution_authority":False})
  if i and i%10==0:time.sleep(.25)
 return {"revision":"USLS_076","program_id":CORRECT_PROGRAM,"selected_count":len(sigs),
  "hydrated_count":sum(x["hydrated"] for x in rows),"rows":rows,
  "rpc_source":"configured" if os.environ.get("SOLANA_RPC_URL") else "public_fallback",
  "execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_damm_v1_deep_transactions.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
