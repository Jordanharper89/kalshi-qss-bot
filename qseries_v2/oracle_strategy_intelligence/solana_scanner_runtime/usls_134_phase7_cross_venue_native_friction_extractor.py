from __future__ import annotations
import json,math
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows_repaired.json"
FEE_KEYS=("fee","fee_lamports","protocol_fee_raw","lp_fee_raw","priority_fee",
 "priority_fee_lamports","dex_fee_delta_lamports","helio_fee_delta_lamports")
RESERVE_KEYS=("pool_base_token_reserves_raw","pool_quote_token_reserves_raw",
 "virtual_sol_reserves_after","virtual_token_reserves_after","liquidity","liquidity_usd",
 "reserve_a","reserve_b","reserves_after")
INPUT_KEYS=("input_amount","base_amount","base_quantity")
OUTPUT_KEYS=("output_amount","quote_amount","quote_quantity")

def _walk(x,out):
 if isinstance(x,dict):
  out.append(x)
  for v in x.values():_walk(v,out)
 elif isinstance(x,list):
  for v in x:_walk(v,out)

def _sig(o):return o.get("trade_signature") or o.get("signature")

def _num(v):
 try:
  x=float(v)
  return x if math.isfinite(x) else None
 except Exception:return None

def _first(o,keys):
 for k in keys:
  if k in o and o.get(k) not in (None,""):return o.get(k)
 return None

def run(root):
 root=Path(root)
 econ=json.loads((root/SRC).read_text(encoding="utf-8"))
 cache={};rows=[];fam={}
 for x in econ.get("rows",[]):
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
  fee_e={};liq_e={};inp=None;out=None
  for o in cache[rel].get(str(sig),[]):
   for k in FEE_KEYS:
    if o.get(k) not in (None,""):fee_e[k]=o.get(k)
   for k in RESERVE_KEYS:
    if o.get(k) not in (None,""):liq_e[k]=o.get(k)
   if inp is None:inp=_num(_first(o,INPUT_KEYS))
   if out is None:out=_num(_first(o,OUTPUT_KEYS))
   eco=o.get("economics")
   if isinstance(eco,dict):
    for k in FEE_KEYS:
     if eco.get(k) not in (None,""):fee_e[k]=eco.get(k)
    for k in RESERVE_KEYS:
     if eco.get(k) not in (None,""):liq_e[k]=eco.get(k)
    if inp is None:inp=_num(_first(eco,INPUT_KEYS))
    if out is None:out=_num(_first(eco,OUTPUT_KEYS))
  row={"family":x.get("family"),"trade_signature":sig,
   "market_address":x.get("market_address"),"asset_a":x.get("asset_a"),"asset_b":x.get("asset_b"),
   "effective_price":x.get("effective_price"),"fee_evidence":fee_e,
   "liquidity_evidence":liq_e,"input_amount":inp,"output_amount":out,
   "fee_supported":bool(fee_e),"liquidity_supported":bool(liq_e),
   "execution_authority":False}
  rows.append(row)
  z=fam.setdefault(row["family"],{"rows":0,"fee":0,"liquidity":0})
  z["rows"]+=1;z["fee"]+=row["fee_supported"];z["liquidity"]+=row["liquidity_supported"]
 return {"revision":"USLS_134","row_count":len(rows),"family_support":fam,"rows":rows,
  "normalization_policy":"PRESERVE_NATIVE_FEE_AND_RESERVE_EVIDENCE_WITHOUT_CROSS_ASSET_CONVERSION",
  "next_boundary":"CROSS_VENUE_EXECUTABLE_CANDIDATE_MERGE",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_cross_venue_native_friction.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
