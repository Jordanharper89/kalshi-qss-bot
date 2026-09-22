from __future__ import annotations
import json,time,urllib.request
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_050_raydium_multifamily_swap_registry import PROGRAMS
RPC="https://api.mainnet.solana.com"

def rpc_batch(sigs,retries=5):
 reqs=[{"jsonrpc":"2.0","id":i,"method":"getTransaction","params":[s,{"encoding":"jsonParsed",
  "commitment":"confirmed","maxSupportedTransactionVersion":0}]} for i,s in enumerate(sigs)]
 payload=json.dumps(reqs).encode();last=None
 for n in range(retries):
  try:
   req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json"})
   with urllib.request.urlopen(req,timeout=20) as r:body=json.loads(r.read())
   by={int(x["id"]):x.get("result") for x in body if "id" in x}
   return [by.get(i) for i in range(len(sigs))]
  except Exception as e:
   last=e;time.sleep(min(n+1,4))
 raise RuntimeError(f"RPC_BATCH_RETRY_EXHAUSTED:{type(last).__name__}:{last}")

def hydrate(root,per_venue=12):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"multidex_live_event_router.json").read_text(encoding="utf-8"))
 chosen={}
 for venue in PROGRAMS:
  sigs=[]
  for x in src["rows"]:
   if x["venue"]==venue and x.get("signature") and x["signature"] not in sigs:sigs.append(x["signature"])
   if len(sigs)>=per_venue:break
  chosen[venue]=sigs
 all_sigs=[];owner={}
 for venue,sigs in chosen.items():
  for s in sigs:
   if s not in owner:owner[s]=venue;all_sigs.append(s)
 vals=rpc_batch(all_sigs) if all_sigs else []
 rows=[{"venue":owner[s],"program_id":PROGRAMS[owner[s]],"signature":s,
  "transaction":tx,"hydrated":tx is not None,"execution_authority":False}
  for s,tx in zip(all_sigs,vals)]
 return {"revision":"USLS_051","requested_count":len(all_sigs),
  "hydrated_count":sum(x["hydrated"] for x in rows),"selected_by_venue":chosen,
  "rows":rows,"batched_rpc":True,"execution_authority":False,"read_only":True}

def write(root):
 d=hydrate(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/raydium_multifamily_transactions.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
