from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_050_raydium_multifamily_swap_registry import classify,PROGRAMS
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
ROLE={
"RAYDIUM_V4":{"SWAP_BASE_IN":(1,14,15),"SWAP_BASE_OUT":(1,14,15),"SWAP_BASE_IN_V2":(1,6,7),"SWAP_BASE_OUT_V2":(1,6,7)},
"RAYDIUM_CPMM":{"SWAP_BASE_INPUT":(3,4,5),"SWAP_BASE_OUTPUT":(3,4,5)},
"RAYDIUM_CLMM":{"SWAP":(2,3,4),"SWAP_V2":(2,3,4)},
"RAYDIUM_LAUNCHLAB":{}}

def b58d(s):
 n=0
 for c in s:n=n*58+ALPH.index(c)
 b=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
 return b"\0"*(len(s)-len(s.lstrip("1")))+b

def keys(tx):
 ks=(((tx or {}).get("transaction") or {}).get("message") or {}).get("accountKeys") or []
 return [x.get("pubkey") if isinstance(x,dict) else x for x in ks]

def all_ix(tx):
 msg=((tx or {}).get("transaction") or {}).get("message") or {};out=[]
 for i,ix in enumerate(msg.get("instructions") or []):out.append(("top",i,ix))
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  for i,ix in enumerate(g.get("instructions") or []):out.append((f"inner:{g.get('index')}",i,ix))
 return out

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"raydium_family_completion_transactions.json").read_text(encoding="utf-8"));rows=[]
 for r in src["rows"]:
  if not r["hydrated"]:continue
  tx=r["transaction"];ks=keys(tx)
  for level,ordinal,ix in all_ix(tx):
   pid=ix.get("programId")
   if not pid and isinstance(ix.get("programIdIndex"),int) and ix["programIdIndex"]<len(ks):pid=ks[ix["programIdIndex"]]
   if pid!=r["program_id"] or not ix.get("data"):continue
   c=classify(r["venue"],b58d(ix["data"]))
   if not c["is_exact_swap"]:continue
   ac=ix.get("accounts") or [];ac=[ks[a] if isinstance(a,int) and a<len(ks) else a for a in ac]
   spec=ROLE.get(r["venue"],{}).get(c["instruction_name"])
   pool=srca=dsta=None
   if spec and len(ac)>max(spec):pool,srca,dsta=ac[spec[0]],ac[spec[1]],ac[spec[2]]
   rows.append({"venue":r["venue"],"program_id":pid,"signature":r["signature"],
    "level":level,"instruction_ordinal":ordinal,"instruction_name":c["instruction_name"],
    "accounts":ac,"pool":pool,"user_source_token_account":srca,"user_destination_token_account":dsta,
    "pool_role_state":"EXACT" if pool else "PENDING_ACCOUNT_ROLE_SCHEMA",
    "transaction":tx,"execution_authority":False})
 return {"revision":"USLS_056B","row_count":len(rows),
  "venue_counts":{v:sum(x["venue"]==v for x in rows) for v in PROGRAMS},
  "exact_pool_role_counts":{v:sum(x["venue"]==v and x["pool_role_state"]=="EXACT" for x in rows) for v in PROGRAMS},
  "rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/raydium_exact_instruction_pool_roles.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
