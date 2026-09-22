from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_050_raydium_multifamily_swap_registry import PROGRAMS,classify
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
def b58d(s):
 n=0
 for c in s:n=n*58+ALPH.index(c)
 b=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
 return b"\0"*(len(s)-len(s.lstrip("1")))+b

def keys(tx):
 ks=(((tx or {}).get("transaction") or {}).get("message") or {}).get("accountKeys") or []
 return [x.get("pubkey") if isinstance(x,dict) else x for x in ks]

def instructions(tx):
 msg=((tx or {}).get("transaction") or {}).get("message") or {}
 out=list(msg.get("instructions") or [])
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:out+=g.get("instructions") or []
 return out

def decode(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"raydium_multifamily_transactions.json").read_text(encoding="utf-8"))
 rows=[]
 for r in src["rows"]:
  if not r["hydrated"]:continue
  tx=r["transaction"];ks=keys(tx)
  for ixn,ix in enumerate(instructions(tx)):
   pid=ix.get("programId")
   if not pid and isinstance(ix.get("programIdIndex"),int) and ix["programIdIndex"]<len(ks):pid=ks[ix["programIdIndex"]]
   if pid!=r["program_id"] or not ix.get("data"):continue
   c=classify(r["venue"],b58d(ix["data"]))
   if not c["is_exact_swap"]:continue
   ac=ix.get("accounts") or []
   ac=[ks[a] if isinstance(a,int) and a<len(ks) else a for a in ac]
   pi=c["pool_account_index"];pool=ac[pi] if pi<len(ac) else None
   rows.append({"venue":r["venue"],"program_id":pid,"signature":r["signature"],
    "instruction_ordinal":ixn,"instruction_name":c["instruction_name"],
    "pool":pool,"pool_account_index":pi,"accounts":ac,
    "transaction":tx,"decode_status":"EXACT_SWAP_INSTRUCTION","execution_authority":False})
 return {"revision":"USLS_052","exact_swap_instruction_count":len(rows),
  "venue_counts":{v:sum(x["venue"]==v for x in rows) for v in PROGRAMS},
  "rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=decode(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/raydium_exact_swap_instructions.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
