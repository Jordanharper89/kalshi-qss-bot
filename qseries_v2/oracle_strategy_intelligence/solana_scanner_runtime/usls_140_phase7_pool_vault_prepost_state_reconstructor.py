from __future__ import annotations
import json
from pathlib import Path

HYD="runtime_state/solana_opportunities/solana_scanner/phase7_missing_venue_transaction_hydration.json"

def _keys(tx):
 msg=((tx or {}).get("transaction") or {}).get("message") or {}
 out=[]
 for a in msg.get("accountKeys") or []:
  if isinstance(a,str):out.append(a)
  elif isinstance(a,dict):out.append(a.get("pubkey"))
 la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
 if isinstance(la,dict):
  out += la.get("writable") or [];out += la.get("readonly") or []
 return out

def _token_map(rows):
 out={}
 for x in rows:
  try:
   idx=int(x.get("accountIndex"));amt=int((x.get("uiTokenAmount") or {}).get("amount") or 0)
   dec=int((x.get("uiTokenAmount") or {}).get("decimals") or 0)
   out[idx]={"mint":x.get("mint"),"owner":x.get("owner"),"amount_raw":amt,"decimals":dec}
  except Exception:pass
 return out

def run(root):
 root=Path(root);h=json.loads((root/HYD).read_text(encoding="utf-8"))
 rows=[];fam={}
 for x in h.get("rows",[]):
  tx=x.get("transaction")
  if not isinstance(tx,dict):continue
  keys=_keys(tx);pre=_token_map(x.get("pre_token_balances") or []);post=_token_map(x.get("post_token_balances") or [])
  changes=[]
  for idx in sorted(set(pre)|set(post)):
   a=pre.get(idx,{});b=post.get(idx,{})
   ar=a.get("amount_raw",0);br=b.get("amount_raw",0)
   if ar==br:continue
   changes.append({"account_index":idx,"account":keys[idx] if idx<len(keys) else None,
    "mint":b.get("mint") or a.get("mint"),"owner":b.get("owner") or a.get("owner"),
    "pre_amount_raw":ar,"post_amount_raw":br,"delta_raw":br-ar,
    "decimals":b.get("decimals",a.get("decimals"))})
  # Strictly expose balance-changing token accounts; do not label them pool vaults without lineage.
  rows.append({"family":x["family"],"trade_signature":x.get("trade_signature"),
   "market_address":x.get("market_address"),"token_account_changes":changes,
   "changed_token_account_count":len(changes),
   "pool_vault_identity_state":"UNRESOLVED_UNLESS_ACCOUNT_ROLE_LINEAGE_MATCHES",
   "execution_authority":False})
  z=fam.setdefault(x["family"],{"rows":0,"with_token_changes":0})
  z["rows"]+=1;z["with_token_changes"]+=bool(changes)
 return {"revision":"USLS_140","row_count":len(rows),
  "family_support":fam,"rows":rows,
  "liquidity_semantics":"PRE_POST_TOKEN_ACCOUNT_STATE_AVAILABLE_BUT_POOL_VAULT_ROLE_NOT_GUESSED",
  "next_boundary":"LIVE_PROSPECTIVE_MISSING_VENUE_LATENCY_COHORT",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_pool_vault_prepost_state.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
