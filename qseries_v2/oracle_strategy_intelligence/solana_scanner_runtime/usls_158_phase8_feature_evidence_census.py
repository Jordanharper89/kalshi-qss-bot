from __future__ import annotations
import json
from pathlib import Path

ECON="runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows_repaired.json"

FIELD_GROUPS={
 "side":("side","trade_side","direction"),
 "trader":("trader","user","wallet","payer","owner"),
 "fee":("fee","fee_lamports","protocol_fee_raw","lp_fee_raw","priority_fee","priority_fee_lamports"),
 "liquidity":("liquidity","liquidity_usd","pool_base_token_reserves_raw","pool_quote_token_reserves_raw",
              "virtual_sol_reserves_after","virtual_token_reserves_after","reserve_a","reserve_b"),
 "time":("trade_observed_unix","observed_unix","block_time","blockTime"),
 "amounts":("base_quantity","quote_quantity","input_amount","output_amount","base_amount","quote_amount"),
}

def _walk(x,out):
 if isinstance(x,dict):
  out.append(x)
  for v in x.values():_walk(v,out)
 elif isinstance(x,list):
  for v in x:_walk(v,out)

def _sig(o): return o.get("trade_signature") or o.get("signature")

def run(root):
 root=Path(root)
 econ=json.loads((root/ECON).read_text(encoding="utf-8"))
 cache={};family={}
 for x in econ.get("rows",[]):
  fam=x.get("family");sig=x.get("trade_signature");rel=x.get("source_artifact")
  if not fam or not sig or not rel:continue
  if rel not in cache:
   try:
    raw=json.loads((root/rel).read_text(encoding="utf-8"))
    objs=[];_walk(raw,objs);idx={}
    for o in objs:
     if isinstance(o,dict) and _sig(o):idx.setdefault(str(_sig(o)),[]).append(o)
    cache[rel]=idx
   except Exception:cache[rel]={}
  z=family.setdefault(fam,{"rows":0,**{k:0 for k in FIELD_GROUPS}})
  z["rows"]+=1
  matches=cache[rel].get(str(sig),[])
  merged={}
  for o in matches: merged.update(o)
  merged.update({k:v for k,v in x.items() if v is not None})
  for g,keys in FIELD_GROUPS.items():
   z[g]+=any(merged.get(k) not in (None,"") for k in keys)
 return {"revision":"USLS_158","family_feature_support":family,
  "family_count":len(family),
  "feature_groups":list(FIELD_GROUPS),
  "next_boundary":"ENRICHED_LEAKAGE_SAFE_FEATURE_SNAPSHOTS",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_feature_evidence_census.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
