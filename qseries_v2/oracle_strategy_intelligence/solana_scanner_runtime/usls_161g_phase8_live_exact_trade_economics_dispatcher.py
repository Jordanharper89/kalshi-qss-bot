from __future__ import annotations
import asyncio,base64,importlib,inspect,json,time
from pathlib import Path

PROV="runtime_state/solana_opportunities/solana_scanner/phase8_family_semantic_decoder_provenance_gate.json"

PROGRAMS={
 "PUMP_FUN":"6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
 "PUMP_SWAP":"pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA",
 "RAYDIUM_LAUNCHLAB":"LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj",
 "RAYDIUM_V4":"675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
 "RAYDIUM_CLMM":"CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK",
 "RAYDIUM_CPMM":"CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C",
 "METEORA_DBC":"dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN",
 "METEORA_DAMM_V1":"Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB",
 "METEORA_DAMM_V2":"cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG",
 "METEORA_DLMM":"LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo",
 "ORCA":"whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",
 "MOONIT":"MoonCVVNZFSYkqNXP6bxHLPL6QQJiMagDL3qcqUQTrG",
 "BOOP_FUN":"boop8hVGQGqehUK2iVEMEnMrL5RbjywRzHKBmBE7ry4",
 "HEAVEN":"HEAVENoP2qxoeuF8Dj2oT1GHEnu49U5mJYkdeC8BAX2o",
}
MARKET_KEYS=("market_address","pool","pool_address","curve","curve_address","bonding_curve")
PRICE_KEYS=("effective_price","price","price_usd","execution_price")
FAMILY_KEYS=("family","venue","program_family","source_family")
SIG_KEYS=("signature","trade_signature")
TIME_KEYS=("observed_unix","trade_observed_unix","received_unix","scanner_observed_unix","block_time")

def _rpc(method,params,timeout=20.0):
 from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
 return _rpc(method,params,timeout)

def _first(x,keys):
 if not isinstance(x,dict):return None
 for k in keys:
  if x.get(k) not in (None,""):return x.get(k)
 return None

def _rows(v):
 if isinstance(v,list):return v
 if isinstance(v,dict):
  for k in ("rows","events","notifications","captured","raw_rows"):
   if isinstance(v.get(k),list):return v[k]
 return []

def _keys(tx):
 msg=((tx or {}).get("transaction") or {}).get("message") or {};out=[]
 for a in msg.get("accountKeys") or []:
  out.append(a if isinstance(a,str) else a.get("pubkey"))
 la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
 if isinstance(la,dict):out+=(la.get("writable") or [])+(la.get("readonly") or [])
 return out

def _instructions(tx,pid):
 keys=_keys(tx);out=[]
 msg=((tx or {}).get("transaction") or {}).get("message") or {}
 for ix in msg.get("instructions") or []:
  if not isinstance(ix,dict):continue
  prog=ix.get("programId")
  if prog is None and ix.get("programIdIndex") is not None:
   try:prog=keys[int(ix["programIdIndex"])]
   except Exception:prog=None
  if prog==pid:out.append(ix)
 meta=(tx or {}).get("meta") or {}
 for g in meta.get("innerInstructions") or []:
  for ix in g.get("instructions") or []:
   if not isinstance(ix,dict):continue
   prog=ix.get("programId")
   if prog is None and ix.get("programIdIndex") is not None:
    try:prog=keys[int(ix["programIdIndex"])]
    except Exception:prog=None
   if prog==pid:out.append(ix)
 return out

def _walk(x,out):
 if isinstance(x,dict):
  out.append(x)
  for v in x.values():_walk(v,out)
 elif isinstance(x,list):
  for v in x:_walk(v,out)

def _extract_econ(obj):
 objs=[];_walk(obj,objs)
 market=price=None
 for o in objs:
  if market is None:market=_first(o,MARKET_KEYS)
  if price is None:price=_first(o,PRICE_KEYS)
  if market is not None and price is not None:break
 try:price=float(price) if price is not None else None
 except Exception:price=None
 return market,price

def _invoke(fn,param_name,ix,raw,tx):
 data=ix.get("data") if isinstance(ix,dict) else None
 name=(param_name or "").lower()
 if "encoded" in name or name in ("data","payload","instruction_data"):
  if data is None:return None
  return fn(data)
 if "row" in name or "record" in name or "event" in name:
  payload=dict(raw);payload["transaction"]=tx;payload["instruction"]=ix
  return fn(payload)
 if "tx" in name or "transaction" in name:
  return fn(tx)
 return None

async def _capture(seconds,max_rows):
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router import capture
 return await capture(seconds=seconds,max_rows=max_rows)

def capture_and_decode(root,seconds=12,max_rows=6000,max_per_family=6):
 root=Path(root)
 prov=json.loads((root/PROV).read_text(encoding="utf-8"))
 selected={f:r.get("selected") for f,r in prov.get("family_results",{}).items() if r.get("selected")}
 ret=asyncio.run(_capture(seconds,max_rows));rawrows=_rows(ret)
 chosen={};seen=set()
 for r in rawrows:
  f=str(_first(r,FAMILY_KEYS) or "").upper();sig=_first(r,SIG_KEYS)
  if f not in selected or not sig or sig in seen:continue
  if len(chosen.get(f,[]))>=max_per_family:continue
  chosen.setdefault(f,[]).append(r);seen.add(sig)
 decoded=[]
 for f,rows in chosen.items():
  c=selected[f];mod=importlib.import_module(c["module"]);fn=getattr(mod,c["function"])
  params=list(inspect.signature(fn).parameters)
  if len(params)!=1:continue
  pid=PROGRAMS.get(f)
  for r in rows:
   sig=_first(r,SIG_KEYS);tx=None
   try:
    tx=_rpc("getTransaction",[sig,{"commitment":"confirmed","encoding":"jsonParsed",
      "maxSupportedTransactionVersion":1}],20.0)
   except Exception:pass
   if not isinstance(tx,dict):continue
   best=None;err=None
   for ix in _instructions(tx,pid):
    try:
     got=_invoke(fn,params[0],ix,r,tx)
     market,price=_extract_econ(got)
     if market is not None or price is not None:
      best={"decoder_output":got,"market_address":market,"effective_price":price};break
    except Exception as e:err=repr(e)
   obs=_first(r,TIME_KEYS) or time.time()
   decoded.append({"family":f,"trade_signature":sig,"observed_unix":obs,
    "market_address":None if best is None else best["market_address"],
    "effective_price":None if best is None else best["effective_price"],
    "decoder_module":c["module"],"decoder_function":c["function"],
    "decoder_error":err,"execution_authority":False})
 return rawrows,decoded

def run(root):
 raw,rows=capture_and_decode(root)
 by={}
 for x in rows:
  z=by.setdefault(x["family"],{"rows":0,"market":0,"price":0,"fully_observable":0})
  z["rows"]+=1;z["market"]+=x["market_address"] is not None;z["price"]+=x["effective_price"] is not None
  z["fully_observable"]+=(x["market_address"] is not None and x["effective_price"] is not None)
 ready=sorted(f for f,v in by.items() if v["fully_observable"]>0)
 return {"revision":"USLS_161G","raw_row_count":len(raw),"decoded_attempt_count":len(rows),
  "family_support":by,"ready_family_count":len(ready),"ready_families":ready,"rows":rows,
  "next_boundary":("PROSPECTIVE_SETUP_FREEZE" if ready else
   "DECODER_OUTPUT_DOES_NOT_YET_EXPOSE_MARKET_AND_PRICE_REPAIR_EXACT_OUTPUT_MAPPING"),
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_live_exact_trade_economics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
