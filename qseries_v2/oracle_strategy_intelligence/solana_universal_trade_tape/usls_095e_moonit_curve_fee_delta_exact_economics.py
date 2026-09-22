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

def lamport_delta(tx,acct):
 ks=keys(tx);m=(tx or {}).get("meta") or {}
 pre=m.get("preBalances") or [];post=m.get("postBalances") or []
 if acct not in ks:return None
 i=ks.index(acct)
 if i>=len(pre) or i>=len(post):return None
 return int(post[i])-int(pre[i])

def token_meta(tx):
 ks=keys(tx);out={}
 for n in ("preTokenBalances","postTokenBalances"):
  for x in ((tx or {}).get("meta") or {}).get(n) or []:
   i=x.get("accountIndex");u=x.get("uiTokenAmount") or {}
   if isinstance(i,int) and i<len(ks) and x.get("mint"):
    out[ks[i]]={"mint":x["mint"],"decimals":int(u.get("decimals") or 0)}
 return out

def token_flows(tx,p,tm):
 out=[]
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  if g.get("index")!=p:continue
  for ix in g.get("instructions") or []:
   q=ix.get("parsed")
   if not isinstance(q,dict) or q.get("type") not in ("transfer","transferChecked","transferCheckedWithFee"):continue
   i=q.get("info") or {}
   if i.get("lamports") is not None:continue
   s=i.get("source");d=i.get("destination");ta=i.get("tokenAmount")
   if isinstance(ta,dict) and ta.get("amount") is not None:
    amt=int(ta["amount"])/(10**int(ta.get("decimals") or 0))
   elif i.get("amount") is not None and (tm.get(s) or tm.get(d)):
    z=tm.get(s) or tm.get(d);amt=int(i["amount"])/(10**z["decimals"])
   else:amt=None
   out.append((s,d,amt))
 return out

def total(rows,s,d):
 v=[a for x,y,a in rows if x==s and y==d and a is not None]
 return sum(v) if v else None

def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((b/"remaining_venue_exact_account_roles.json").read_text(encoding="utf-8"))
 rows=[]
 for x in src["rows"]:
  if x["venue"]!="MOONIT":continue
  r=x["roles"];tx=x["transaction"];tm=token_meta(tx)
  tf=token_flows(tx,parent(x["level"],x["instruction_ordinal"]),tm)
  curve=lamport_delta(tx,r["curve_account"])
  dex=lamport_delta(tx,r["dex_fee"]);helio=lamport_delta(tx,r["helio_fee"])
  token_in=total(tf,r["sender_token_account"],r["curve_token_account"])
  token_out=total(tf,r["curve_token_account"],r["sender_token_account"])
  if x["side"]=="SELL":
   sol_lamports=(-curve-dex-helio) if None not in (curve,dex,helio) else None
   ia,im=token_in,r["mint"];oa,om=(sol_lamports/1e9 if sol_lamports is not None else None),"NATIVE_SOL"
   economic_rule="SELL_TOKEN_INPUT_PLUS_NET_CURVE_SOL_OUTFLOW_AFTER_PROTOCOL_FEES"
  else:
   sol_lamports=(curve+dex+helio) if None not in (curve,dex,helio) else None
   ia,im=(sol_lamports/1e9 if sol_lamports is not None else None),"NATIVE_SOL";oa,om=token_out,r["mint"]
   economic_rule="BUY_GROSS_SOL_INFLOW_TO_CURVE_AND_PROTOCOL_FEES_PLUS_TOKEN_OUTPUT"
  exact=bool(ia is not None and oa is not None and ia>0 and oa>0)
  rows.append({"signature":x["signature"],"side":x["side"],"market_address":r["curve_account"],"trader":r["sender"],
   "input_asset":im,"input_amount":ia,"output_asset":om,"output_amount":oa,
   "curve_delta_lamports":curve,"dex_fee_delta_lamports":dex,"helio_fee_delta_lamports":helio,
   "economic_rule":economic_rule,
   "decoder_state":"EXACT_MOONIT_CURVE_FEE_DELTA_ECONOMICS" if exact else "MOONIT_CURVE_FEE_RECONCILIATION_PENDING",
   "execution_authority":False})
 return {"revision":"USLS_095E","row_count":len(rows),
  "exact_economic_count":sum(x["decoder_state"].startswith("EXACT_") for x in rows),
  "economics_source":"EXACT_TOKEN_TRANSFER_PLUS_MOONIT_ROLE_LAMPORT_DELTAS",
  "rows":rows,"supersedes":["USLS_095","USLS_095C"],"profitability_claimed":False,
  "execution_authority":False,"read_only":True}

def write(root):
 d=build(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/moonit_exact_economics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
