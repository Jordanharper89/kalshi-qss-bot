from __future__ import annotations
import json,time,urllib.request
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_050_raydium_multifamily_swap_registry import PROGRAMS
RPC="https://api.mainnet.solana.com"

def rpc(method,params,retries=5):
 payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode();last=None
 for n in range(retries):
  try:
   req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json"})
   with urllib.request.urlopen(req,timeout=20) as r:return json.loads(r.read()).get("result")
  except Exception as e:
   last=e;time.sleep(min(1+n,4))
 return None

def hydrate_sig(sig):
 return rpc("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":0}])

def recent_sigs(program,limit=24):
 r=rpc("getSignaturesForAddress",[program,{"limit":limit,"commitment":"confirmed"}]) or []
 return [x["signature"] for x in r if x.get("signature") and x.get("err") is None]

def build(root,target_per_venue=12):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 router=json.loads((base/"multidex_live_event_router.json").read_text(encoding="utf-8"))
 selected={}
 for venue,pid in PROGRAMS.items():
  sigs=[]
  for x in router["rows"]:
   s=x.get("signature")
   if x.get("venue")==venue and s and s not in sigs:sigs.append(s)
   if len(sigs)>=target_per_venue:break
  if len(sigs)<target_per_venue:
   for s in recent_sigs(pid,target_per_venue*3):
    if s not in sigs:sigs.append(s)
    if len(sigs)>=target_per_venue:break
  selected[venue]=sigs
 rows=[]
 for venue,sigs in selected.items():
  for s in sigs:
   tx=hydrate_sig(s)
   rows.append({"venue":venue,"program_id":PROGRAMS[venue],"signature":s,
    "transaction":tx,"hydrated":tx is not None,"execution_authority":False})
 return {"revision":"USLS_055B","selected_counts":{k:len(v) for k,v in selected.items()},
  "hydrated_counts":{v:sum(x["venue"]==v and x["hydrated"] for x in rows) for v in PROGRAMS},
  "rows":rows,"fallback_recent_signatures":True,"retry_safe":True,
  "execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/raydium_family_completion_transactions.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
