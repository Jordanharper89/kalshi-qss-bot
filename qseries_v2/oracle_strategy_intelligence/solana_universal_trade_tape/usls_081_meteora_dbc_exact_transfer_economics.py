from __future__ import annotations
import json
from pathlib import Path

def parent(level,ordinal): return int(str(level).split(":",1)[1]) if str(level).startswith("inner:") else int(ordinal)
def keys(tx):
 m=((tx or {}).get("transaction") or {}).get("message") or {}
 ks=[x.get("pubkey") if isinstance(x,dict) else x for x in m.get("accountKeys") or []]
 la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
 return ks+(la.get("writable") or [])+(la.get("readonly") or [])
def meta(tx):
 ks=keys(tx);o={}
 for name in ("preTokenBalances","postTokenBalances"):
  for x in ((tx or {}).get("meta") or {}).get(name) or []:
   i=x.get("accountIndex");u=x.get("uiTokenAmount") or {}
   if isinstance(i,int) and i<len(ks) and x.get("mint"):
    o[ks[i]]={"mint":x["mint"],"decimals":int(u.get("decimals") or 0)}
 return o
def trs(tx,p,tm):
 out=[]
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  if g.get("index")!=p: continue
  for ix in g.get("instructions") or []:
   q=ix.get("parsed")
   if not isinstance(q,dict) or q.get("type") not in ("transfer","transferChecked","transferCheckedWithFee"): continue
   i=q.get("info") or {};s=i.get("source");d=i.get("destination");ta=i.get("tokenAmount")
   if isinstance(ta,dict) and ta.get("amount") is not None: a=int(ta["amount"])/(10**int(ta.get("decimals") or 0))
   elif i.get("amount") is not None and (s in tm or d in tm):
    dec=(tm.get(s) or tm.get(d))["decimals"];a=int(i["amount"])/(10**dec)
   else:a=None
   out.append((s,d,a))
 return out
def amount(ts,s,d):
 v=[a for x,y,a in ts if x==s and y==d and a is not None];return sum(v) if v else None

def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((b/"meteora_orca_exact_swap_instructions.json").read_text(encoding="utf-8"));rows=[]
 for x in src["rows"]:
  if x["venue"]!="METEORA_DBC":continue
  a=x["accounts"];tx=x["transaction"]
  if len(a)<10:continue
  tm=meta(tx);t=trs(tx,parent(x["level"],x["instruction_ordinal"]),tm)
  pool,user_in,user_out,bv,qv,bm,qm,payer=a[2],a[3],a[4],a[5],a[6],a[7],a[8],a[9]
  bi=amount(t,user_in,bv);qi=amount(t,user_in,qv);bo=amount(t,bv,user_out);qo=amount(t,qv,user_out)
  e=None
  if bi and qo:e={"input_mint":bm,"input_amount":bi,"output_mint":qm,"output_amount":qo}
  elif qi and bo:e={"input_mint":qm,"input_amount":qi,"output_mint":bm,"output_amount":bo}
  rows.append({"signature":x["signature"],"instruction_name":x["instruction_name"],"pool":pool,"trader":payer,
   "economics":e,"decoder_state":"EXACT_DBC_INSTRUCTION_ECONOMICS" if e else "DBC_RECONCILIATION_PENDING","execution_authority":False})
 return {"revision":"USLS_081","row_count":len(rows),"exact_economic_count":sum(x["economics"] is not None for x in rows),
  "rows":rows,"profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_dbc_exact_economics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
