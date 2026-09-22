from __future__ import annotations
import json
from pathlib import Path

DELTAS="runtime_state/solana_opportunities/solana_scanner/phase7_live_token_account_deltas.json"
SEARCH="runtime_state/solana_opportunities"

ROLE_KEYS=("token_vault","quote_vault","a_token_vault","b_token_vault","vault_a","vault_b",
 "user_source_token_account","user_destination_token_account")

def _walk(x,out):
 if isinstance(x,dict):
  out.append(x)
  for v in x.values():_walk(v,out)
 elif isinstance(x,list):
  for v in x:_walk(v,out)

def run(root):
 root=Path(root);d=json.loads((root/DELTAS).read_text(encoding="utf-8"))
 known={}
 for p in (root/SEARCH).rglob("*.json"):
  if p.stat().st_size>80_000_000:continue
  try:raw=json.loads(p.read_text(encoding="utf-8"))
  except Exception:continue
  objs=[];_walk(raw,objs)
  for o in objs:
   if not isinstance(o,dict):continue
   fam=o.get("family") or o.get("venue") or o.get("launcher_family")
   if not fam:continue
   f=str(fam).upper()
   for k in ROLE_KEYS:
    v=o.get(k)
    if isinstance(v,str) and len(v)>20:
     known.setdefault(f,{}).setdefault(v,set()).add(k)
 rows=[];fam={}
 for x in d.get("rows",[]):
  f=x["family"];km=known.get(f,{})
  matches=[]
  for c in x.get("token_account_changes",[]):
   acct=c.get("account")
   if acct in km:
    matches.append({"account":acct,"roles":sorted(km[acct]),"mint":c.get("mint"),
     "pre_amount_raw":c.get("pre_amount_raw"),"post_amount_raw":c.get("post_amount_raw"),
     "delta_raw":c.get("delta_raw"),"decimals":c.get("decimals")})
  rows.append({"family":f,"trade_signature":x["trade_signature"],
   "certified_role_matches":matches,"certified_role_match_count":len(matches),
   "execution_authority":False})
  z=fam.setdefault(f,{"rows":0,"with_role_match":0,"matched_accounts":0})
  z["rows"]+=1;z["with_role_match"]+=bool(matches);z["matched_accounts"]+=len(matches)
 return {"revision":"USLS_145","row_count":len(rows),"family_support":fam,"rows":rows,
  "match_policy":"ONLY_EXACT_ACCOUNT_ADDRESS_MATCH_TO_EXISTING_CERTIFIED_ROLE_ARTIFACTS",
  "next_boundary":"LIVE_FRICTION_NORMALIZATION_FROM_CERTIFIED_ROLES",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_certified_vault_role_match.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
