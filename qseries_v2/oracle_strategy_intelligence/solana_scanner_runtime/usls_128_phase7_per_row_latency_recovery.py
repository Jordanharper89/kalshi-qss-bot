from __future__ import annotations
import json
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows_repaired.json"

def _walk(x,out):
 if isinstance(x,dict):
  out.append(x)
  for v in x.values():_walk(v,out)
 elif isinstance(x,list):
  for v in x:_walk(v,out)

def _sig(x):return x.get("trade_signature") or x.get("signature")

def run(root):
 root=Path(root);d=json.loads((root/SRC).read_text(encoding="utf-8"))
 cache={};rows=[];by={}
 for x in d.get("rows",[]):
  rel=x.get("source_artifact");sig=x.get("trade_signature")
  if not rel or not sig:continue
  if rel not in cache:
   try:
    raw=json.loads((root/rel).read_text(encoding="utf-8"))
    objs=[];_walk(raw,objs);idx={}
    for o in objs:
     if isinstance(o,dict) and _sig(o):idx.setdefault(str(_sig(o)),[]).append(o)
    cache[rel]=idx
   except Exception:cache[rel]={}
  block=None;obs=x.get("trade_observed_unix")
  for o in cache[rel].get(str(sig),[]):
   if block is None:block=o.get("block_time") or o.get("blockTime")
   if obs is None:obs=o.get("observed_unix") or o.get("trade_observed_unix") or o.get("received_unix")
  latency=None
  if isinstance(block,(int,float)) and isinstance(obs,(int,float)):
   latency=max(0.0,float(obs)-float(block))
  row={"family":x.get("family"),"market_address":x.get("market_address"),
       "trade_signature":sig,"block_time":block,"observed_unix":obs,
       "observation_latency_seconds":latency,"execution_authority":False}
  rows.append(row)
  z=by.setdefault(row["family"],{"rows":0,"latency":0})
  z["rows"]+=1;z["latency"]+=latency is not None
 return {"revision":"USLS_128","row_count":len(rows),
  "latency_row_count":sum(x["observation_latency_seconds"] is not None for x in rows),
  "family_support":by,"rows":rows,
  "latency_semantics":"CHAIN_BLOCK_TIME_TO_ORACLE_OBSERVATION_TIME",
  "next_boundary":"PRE_TRADE_REFERENCE_AND_EXECUTION_DEVIATION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_per_row_latency_recovery.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
