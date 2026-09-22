from __future__ import annotations
import json
from pathlib import Path
def keys(tx):
 m=((tx or {}).get("transaction") or {}).get("message") or {}
 ks=[x.get("pubkey") if isinstance(x,dict) else x for x in m.get("accountKeys") or []]
 la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
 return ks+(la.get("writable") or [])+(la.get("readonly") or [])
def delta(tx,acct):
 ks=keys(tx);m=(tx or {}).get("meta") or {};pre=m.get("preBalances") or [];post=m.get("postBalances") or []
 if acct not in ks:return None
 i=ks.index(acct)
 if i>=len(pre) or i>=len(post):return None
 return (post[i]-pre[i])/1_000_000_000
def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((b/"remaining_venue_exact_account_roles.json").read_text(encoding="utf-8"));rows=[]
 for x in src["rows"]:
  if x["venue"]!="MOONIT" or x["side"]!="SELL":continue
  r=x["roles"];tx=x["transaction"];ks=keys(tx);fee=((tx or {}).get("meta") or {}).get("fee",0)/1_000_000_000
  payer=ks[0] if ks else None
  rows.append({"signature":x["signature"],"sender":r["sender"],"fee_payer":payer,"tx_fee_sol":fee,
   "sender_delta_sol":delta(tx,r["sender"]),"curve_delta_sol":delta(tx,r["curve_account"]),
   "dex_fee_delta_sol":delta(tx,r["dex_fee"]),"helio_fee_delta_sol":delta(tx,r["helio_fee"]),
   "sender_is_fee_payer":r["sender"]==payer,"execution_authority":False})
 return {"revision":"USLS_095B","sell_rows":len(rows),"rows":rows,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/moonit_sell_lamport_lineage_diagnostic.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
