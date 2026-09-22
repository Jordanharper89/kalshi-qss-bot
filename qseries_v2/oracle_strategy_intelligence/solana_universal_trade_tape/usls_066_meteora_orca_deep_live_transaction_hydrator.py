from __future__ import annotations
import json,os,time,urllib.request
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_065_meteora_orca_official_swap_registry import PROGRAMS
RPC=os.environ.get("SOLANA_RPC_URL","https://api.mainnet.solana.com")

def rpc(method,params,retries=6):
 payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
 for n in range(retries):
  try:
   req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json","User-Agent":"qseries-usls066"})
   with urllib.request.urlopen(req,timeout=20) as r:return json.loads(r.read()).get("result")
  except Exception:time.sleep(min(1.5*(n+1),6))
 return None

def sigs(pid,limit=30):
 r=rpc("getSignaturesForAddress",[pid,{"limit":limit,"commitment":"confirmed"}]) or []
 return [x["signature"] for x in r if x.get("signature") and x.get("err") is None]

def tx(sig):
 return rpc("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":0}])

def build(root):
 rows=[]
 for venue,pid in PROGRAMS.items():
  for s in sigs(pid):
   t=tx(s);rows.append({"venue":venue,"program_id":pid,"signature":s,"transaction":t,
    "hydrated":t is not None,"execution_authority":False})
   time.sleep(.05)
 return {"revision":"USLS_066","selected_counts":{v:sum(x["venue"]==v for x in rows) for v in PROGRAMS},
  "hydrated_counts":{v:sum(x["venue"]==v and x["hydrated"] for x in rows) for v in PROGRAMS},
  "rows":rows,"rpc_source":"configured" if os.environ.get("SOLANA_RPC_URL") else "public_fallback",
  "execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_orca_deep_transactions.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
