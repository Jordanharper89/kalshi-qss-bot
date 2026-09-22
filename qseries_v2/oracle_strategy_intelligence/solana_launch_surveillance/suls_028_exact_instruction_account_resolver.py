from __future__ import annotations
import json
from pathlib import Path
TARGETS={"dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN","cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"}

def _keys(raw):
 msg=((raw.get("transaction") or {}).get("message") or {});out=[]
 for x in msg.get("accountKeys") or []:
  out.append(x if isinstance(x,str) else x.get("pubkey") if isinstance(x,dict) else None)
 meta=raw.get("meta") or {};loaded=meta.get("loadedAddresses") or {}
 out.extend(loaded.get("writable") or []);out.extend(loaded.get("readonly") or [])
 return out

def _resolve(ix,keys):
 if not isinstance(ix,dict):return None
 pid=ix.get("programId")
 if not pid and isinstance(ix.get("programIdIndex"),int) and ix["programIdIndex"]<len(keys):pid=keys[ix["programIdIndex"]]
 acc=[]
 for a in ix.get("accounts") or []:
  if isinstance(a,int) and a<len(keys):acc.append(keys[a])
  elif isinstance(a,str):acc.append(a)
 return {"program_id":pid,"accounts":acc,"data":ix.get("data"),"parsed":ix.get("parsed")}

def run(root):
 d=json.loads((root/"runtime_state/solana_opportunities/launch_surveillance/exact_candidate_transaction.json").read_text(encoding="utf-8"))
 rows=[]
 for t in d.get("transactions",[]):
  e=t.get("envelope") or {};raw=e.get("raw_transaction") or {};keys=_keys(raw);found=[]
  msg=((raw.get("transaction") or {}).get("message") or {})
  for ix in msg.get("instructions") or []:
   r=_resolve(ix,keys)
   if r and r["program_id"] in TARGETS:found.append({"level":"outer",**r})
  for grp in (raw.get("meta") or {}).get("innerInstructions") or []:
   for ix in grp.get("instructions") or []:
    r=_resolve(ix,keys)
    if r and r["program_id"] in TARGETS:found.append({"level":"inner","parent_index":grp.get("index"),**r})
  rows.append({"signature":e.get("signature"),"slot":e.get("slot"),"account_keys":keys,"target_instructions":found})
 return {"revision":"SULS_028","rows":rows,"target_instruction_count":sum(len(x["target_instructions"]) for x in rows),"execution_authority":False}
def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/exact_instruction_accounts.json";p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
