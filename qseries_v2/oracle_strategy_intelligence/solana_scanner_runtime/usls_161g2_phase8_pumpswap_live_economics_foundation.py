from __future__ import annotations
import asyncio,json,time
from pathlib import Path

PUMPSWAP="pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"

def _rpc(method,params,timeout=20.0):
 from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
 last=None
 for delay in (0.0,0.7,1.4,2.8):
  if delay:time.sleep(delay)
  try:return _rpc(method,params,timeout)
  except Exception as e:last=e
 raise last

def _rows(v):
 if isinstance(v,list):return v
 if isinstance(v,dict):
  for k in ("rows","events","notifications","captured","raw_rows"):
   if isinstance(v.get(k),list):return v[k]
 return []

def _first(x,*keys):
 if not isinstance(x,dict):return None
 for k in keys:
  v=x.get(k)
  if v not in (None,""):return v
 return None

def _keys(tx):
 msg=((tx or {}).get("transaction") or {}).get("message") or {};out=[]
 for a in msg.get("accountKeys") or []:
  out.append(a if isinstance(a,str) else a.get("pubkey"))
 la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
 if isinstance(la,dict):out+=(la.get("writable") or [])+(la.get("readonly") or [])
 return out

def _ixs(tx):
 keys=_keys(tx);out=[]
 msg=((tx or {}).get("transaction") or {}).get("message") or {}
 def add(ix,level,parent=None):
  if not isinstance(ix,dict):return
  pid=ix.get("programId")
  if pid is None and ix.get("programIdIndex") is not None:
   try:pid=keys[int(ix["programIdIndex"])]
   except Exception:pid=None
  if pid!=PUMPSWAP:return
  accts=[]
  for a in ix.get("accounts") or []:
   if isinstance(a,str):accts.append(a)
   else:
    try:accts.append(keys[int(a)])
    except Exception:pass
  out.append({"level":level,"parent":parent,"accounts":accts,"data":ix.get("data")})
 for i,ix in enumerate(msg.get("instructions") or []):add(ix,"outer",i)
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  for ix in g.get("instructions") or []:add(ix,"inner",g.get("index"))
 return out

def _tokmap(rows):
 out={}
 for x in rows or []:
  try:
   u=x.get("uiTokenAmount") or {}
   out[int(x["accountIndex"])]={"mint":x.get("mint"),
    "amount":int(u.get("amount") or 0),"decimals":int(u.get("decimals") or 0)}
  except Exception:pass
 return out

def _economics(tx,ix):
 keys=_keys(tx);meta=(tx or {}).get("meta") or {}
 pre=_tokmap(meta.get("preTokenBalances"));post=_tokmap(meta.get("postTokenBalances"))
 allowed=set(ix.get("accounts") or []);changes=[]
 for idx in sorted(set(pre)|set(post)):
  acct=keys[idx] if idx<len(keys) else None
  if acct not in allowed:continue
  a=pre.get(idx,{});b=post.get(idx,{})
  ar=a.get("amount",0);br=b.get("amount",0);delta=br-ar
  mint=b.get("mint") or a.get("mint");dec=b.get("decimals",a.get("decimals"))
  if not mint or not delta:continue
  ui=delta/(10**dec)
  changes.append({"account":acct,"mint":mint,"decimals":dec,"delta_ui":ui,
                  "pre_raw":ar,"post_raw":br})
 # Aggregate instruction-local token flow by mint.
 by={}
 for c in changes:by[c["mint"]]=by.get(c["mint"],0.0)+c["delta_ui"]
 nz=[(m,v) for m,v in by.items() if abs(v)>0]
 if len(nz)<2:return None
 pos=sorted([(m,v) for m,v in nz if v>0],key=lambda z:abs(z[1]),reverse=True)
 neg=sorted([(m,v) for m,v in nz if v<0],key=lambda z:abs(z[1]),reverse=True)
 if not pos or not neg:return None
 out_m,out_amt=pos[0];in_m,in_amt=neg[0]
 price=abs(out_amt/in_amt) if in_amt else None
 pair="PUMP_SWAP:"+in_m+"->"+out_m
 return {"market_key":pair,"input_mint":in_m,"output_mint":out_m,
  "input_amount":abs(in_amt),"output_amount":abs(out_amt),
  "effective_output_per_input":price,"token_changes":changes}

async def _capture():
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router import capture
 return await capture(seconds=12,max_rows=9000)

def run(root):
 from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_045b_universal_multidex_decoder_framework import decode_pumpswap_program_data
 ret=asyncio.run(_capture());raw=_rows(ret);seen=set();chosen=[]
 for r in raw:
  fam=str(_first(r,"family","venue","program_family","source_family") or "").upper()
  sig=_first(r,"signature","trade_signature")
  if fam=="PUMP_SWAP" and sig and sig not in seen:
   chosen.append(r);seen.add(sig)
  if len(chosen)>=12:break
 rows=[]
 for r in chosen:
  sig=_first(r,"signature","trade_signature")
  try:tx=_rpc("getTransaction",[sig,{"commitment":"confirmed","encoding":"jsonParsed",
      "maxSupportedTransactionVersion":1}],20.0)
  except Exception:continue
  if not isinstance(tx,dict):continue
  for ix in _ixs(tx):
   data=ix.get("data")
   if not data:continue
   try:decoded=decode_pumpswap_program_data(data)
   except Exception:decoded=None
   if decoded is None:continue
   eco=_economics(tx,ix)
   if eco:
    rows.append({"family":"PUMP_SWAP","trade_signature":sig,
     "observed_unix":_first(r,"observed_unix","trade_observed_unix","received_unix") or time.time(),
     "exact_pumpswap_instruction_decoded":True,**eco,
     "market_identity_semantics":"DIRECTED_MINT_PAIR_NOT_POOL_ADDRESS",
     "price_semantics":"INSTRUCTION_LOCAL_OUTPUT_PER_INPUT_TOKEN_FLOW",
     "execution_authority":False})
    break
 bypair={}
 for x in rows:bypair[x["market_key"]]=bypair.get(x["market_key"],0)+1
 return {"revision":"USLS_161G2","raw_row_count":len(raw),
  "pumpswap_signature_count":len(chosen),"economic_row_count":len(rows),
  "repeat_market_count":sum(v>=2 for v in bypair.values()),
  "market_counts":bypair,"rows":rows,
  "exact_pool_address_claimed":False,
  "next_boundary":("PUMPSWAP_PROSPECTIVE_SETUP_FREEZE_ON_DIRECTED_PAIR"
   if rows else "PUMPSWAP_LIVE_EVENT_TO_TRANSACTION_ECONOMICS_STILL_BROKEN"),
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_pumpswap_live_economics_foundation.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
