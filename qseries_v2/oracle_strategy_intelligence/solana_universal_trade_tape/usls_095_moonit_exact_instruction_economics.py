from __future__ import annotations
import json
from pathlib import Path
NATIVE_SOL="NATIVE_SOL"

def parent(level,ordinal): return int(str(level).split(":",1)[1]) if str(level).startswith("inner:") else int(ordinal)
def keys(tx):
 m=((tx or {}).get("transaction") or {}).get("message") or {}
 ks=[x.get("pubkey") if isinstance(x,dict) else x for x in m.get("accountKeys") or []]
 la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
 return ks+(la.get("writable") or [])+(la.get("readonly") or [])
def tmeta(tx):
 ks=keys(tx);o={}
 for n in ("preTokenBalances","postTokenBalances"):
  for x in ((tx or {}).get("meta") or {}).get(n) or []:
   i=x.get("accountIndex");u=x.get("uiTokenAmount") or {}
   if isinstance(i,int) and i<len(ks) and x.get("mint"):
    o[ks[i]]={"mint":x["mint"],"decimals":int(u.get("decimals") or 0)}
 return o
def transfers(tx,p,tm):
 tok=[];sol=[]
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  if g.get("index")!=p:continue
  for ix in g.get("instructions") or []:
   q=ix.get("parsed")
   if not isinstance(q,dict):continue
   i=q.get("info") or {};typ=q.get("type");s=i.get("source");d=i.get("destination")
   if typ in ("transfer","transferChecked","transferCheckedWithFee") and i.get("lamports") is None:
    ta=i.get("tokenAmount")
    if isinstance(ta,dict) and ta.get("amount") is not None:a=int(ta["amount"])/(10**int(ta.get("decimals") or 0))
    elif i.get("amount") is not None and (tm.get(s) or tm.get(d)):
     z=tm.get(s) or tm.get(d);a=int(i["amount"])/(10**z["decimals"])
    else:a=None
    tok.append((s,d,a))
   if i.get("lamports") is not None and s and d:sol.append((s,d,int(i["lamports"])/1_000_000_000))
 return tok,sol
def total(rows,s,d):
 v=[a for x,y,a in rows if x==s and y==d and a is not None];return sum(v) if v else None

def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((b/"remaining_venue_exact_account_roles.json").read_text(encoding="utf-8"));rows=[]
 for x in src["rows"]:
  if x["venue"]!="MOONIT":continue
  r=x["roles"];tm=tmeta(x["transaction"]);tok,sol=transfers(x["transaction"],parent(x["level"],x["instruction_ordinal"]),tm)
  if x["side"]=="BUY":
   ia=total(sol,r["sender"],r["curve_account"]);oa=total(tok,r["curve_token_account"],r["sender_token_account"])
   im=NATIVE_SOL;om=r["mint"]
  else:
   ia=total(tok,r["sender_token_account"],r["curve_token_account"]);oa=total(sol,r["curve_account"],r["sender"])
   im=r["mint"];om=NATIVE_SOL
  exact=bool(ia is not None and oa is not None and ia>0 and oa>0)
  rows.append({"signature":x["signature"],"side":x["side"],"market_address":r["curve_account"],"trader":r["sender"],
   "input_asset":im,"input_amount":ia,"output_asset":om,"output_amount":oa,
   "decoder_state":"EXACT_MOONIT_INSTRUCTION_ECONOMICS" if exact else "MOONIT_RECONCILIATION_PENDING","execution_authority":False})
 return {"revision":"USLS_095","row_count":len(rows),"exact_economic_count":sum(x["decoder_state"].startswith("EXACT_") for x in rows),
  "rows":rows,"profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/moonit_exact_economics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
