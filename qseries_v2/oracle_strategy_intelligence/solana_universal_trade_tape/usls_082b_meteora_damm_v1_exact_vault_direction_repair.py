from __future__ import annotations
import json
from pathlib import Path

def parent(level,ordinal):
 return int(str(level).split(":",1)[1]) if str(level).startswith("inner:") else int(ordinal)

def keys(tx):
 m=((tx or {}).get("transaction") or {}).get("message") or {}
 ks=[x.get("pubkey") if isinstance(x,dict) else x for x in m.get("accountKeys") or []]
 la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
 return ks+(la.get("writable") or [])+(la.get("readonly") or [])

def token_meta(tx):
 ks=keys(tx);out={}
 for name in ("preTokenBalances","postTokenBalances"):
  for x in ((tx or {}).get("meta") or {}).get(name) or []:
   i=x.get("accountIndex");u=x.get("uiTokenAmount") or {}
   if isinstance(i,int) and i<len(ks) and x.get("mint"):
    out[ks[i]]={"mint":x["mint"],"decimals":int(u.get("decimals") or 0)}
 return out

def transfers(tx,p,tm):
 out=[]
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  if g.get("index")!=p:continue
  for ix in g.get("instructions") or []:
   q=ix.get("parsed")
   if not isinstance(q,dict) or q.get("type") not in ("transfer","transferChecked","transferCheckedWithFee"):continue
   i=q.get("info") or {};s=i.get("source");d=i.get("destination");ta=i.get("tokenAmount")
   if isinstance(ta,dict) and ta.get("amount") is not None:
    amt=int(ta["amount"])/(10**int(ta.get("decimals") or 0))
   elif i.get("amount") is not None:
    z=tm.get(s) or tm.get(d);amt=int(i["amount"])/(10**z["decimals"]) if z else None
   else:amt=None
   out.append({"source":s,"destination":d,"amount":amt})
 return out

def total(ts,s,d):
 vals=[x["amount"] for x in ts if x["source"]==s and x["destination"]==d and x["amount"] is not None]
 return sum(vals) if vals else None

def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((b/"meteora_damm_v1_exact_swaps.json").read_text(encoding="utf-8"));rows=[]
 for x in src["rows"]:
  tm=token_meta(x["transaction"]);ts=transfers(x["transaction"],parent(x["level"],x["instruction_ordinal"]),tm)
  av=x["a_token_vault"];bv=x["b_token_vault"];us=x["user_source"];ud=x["user_destination"]
  a_in=total(ts,us,av);b_in=total(ts,us,bv);a_out=total(ts,av,ud);b_out=total(ts,bv,ud)
  econ=None
  if a_in is not None and b_out is not None:
   am=tm.get(av,{}).get("mint");bm=tm.get(bv,{}).get("mint")
   if am and bm:econ={"input_mint":am,"input_amount":a_in,"output_mint":bm,"output_amount":b_out,"direction":"A_TO_B"}
  elif b_in is not None and a_out is not None:
   bm=tm.get(bv,{}).get("mint");am=tm.get(av,{}).get("mint")
   if bm and am:econ={"input_mint":bm,"input_amount":b_in,"output_mint":am,"output_amount":a_out,"direction":"B_TO_A"}
  rows.append({"signature":x["signature"],"pool":x["pool"],"trader":x["trader"],"economics":econ,
   "decoder_state":"EXACT_DAMM_V1_VAULT_DIRECTION_ECONOMICS" if econ else "VAULT_DIRECTION_RECONCILIATION_PENDING",
   "execution_authority":False})
 return {"revision":"USLS_082B","row_count":len(rows),
  "exact_economic_count":sum(x["economics"] is not None for x in rows),"rows":rows,
  "supersedes":"USLS_082","profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_damm_v1_strict_economics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
