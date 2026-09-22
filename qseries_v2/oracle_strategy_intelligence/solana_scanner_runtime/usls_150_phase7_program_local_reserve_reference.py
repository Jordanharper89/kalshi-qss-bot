from __future__ import annotations
import json
from pathlib import Path
SRC="runtime_state/solana_opportunities/solana_scanner/phase7_program_local_liquidity_candidates.json"

def run(root):
 d=json.loads((Path(root)/SRC).read_text(encoding="utf-8"));rows=[];fam={}
 for x in d.get("rows",[]):
  refs=[]
  for c in x.get("liquidity_candidates",[]):
   accts=[]
   for a in c.get("accounts",[]):
    dec=a.get("decimals")
    pre=a.get("pre_amount_raw");post=a.get("post_amount_raw")
    pre_ui=(pre/(10**dec)) if isinstance(pre,(int,float)) and isinstance(dec,int) else None
    post_ui=(post/(10**dec)) if isinstance(post,(int,float)) and isinstance(dec,int) else None
    accts.append({**a,"pre_amount_ui":pre_ui,"post_amount_ui":post_ui})
   refs.append({"instruction_index":c.get("instruction_index"),
    "parent_index":c.get("parent_index"),"accounts":accts,
    "reference_state":"PROGRAM_LOCAL_PRE_POST_TOKEN_BALANCE_REFERENCE"})
  rows.append({"family":x["family"],"trade_signature":x["trade_signature"],
   "reserve_references":refs,"reference_count":len(refs),
   "reference_is_certified_pool_liquidity":False,"execution_authority":False})
  z=fam.setdefault(x["family"],{"rows":0,"with_reference":0})
  z["rows"]+=1;z["with_reference"]+=bool(refs)
 return {"revision":"USLS_150","row_count":len(rows),"family_support":fam,"rows":rows,
  "reference_semantics":"PROGRAM_LOCAL_TOKEN_BALANCE_REFERENCE_NOT_YET_CERTIFIED_POOL_LIQUIDITY",
  "next_boundary":"EXTENDED_LIVE_COHORT_FOR_UNOBSERVED_FAMILIES",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_program_local_reserve_reference.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
