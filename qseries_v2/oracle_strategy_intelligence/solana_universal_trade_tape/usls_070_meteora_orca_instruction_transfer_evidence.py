from __future__ import annotations
import json
from pathlib import Path

def parent_index(level,ordinal):
 if str(level).startswith("inner:"):
  return int(str(level).split(":",1)[1])
 return int(ordinal)

def transfers(tx,parent):
 out=[]
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  if g.get("index")!=parent:continue
  for ix in g.get("instructions") or []:
   p=ix.get("parsed")
   if not isinstance(p,dict):continue
   typ=p.get("type");info=p.get("info") or {}
   if typ not in ("transfer","transferChecked","transferCheckedWithFee"):continue
   amt=None;dec=None
   ta=info.get("tokenAmount")
   if isinstance(ta,dict) and ta.get("amount") is not None:
    dec=int(ta.get("decimals") or 0);amt=int(ta["amount"])/(10**dec)
   elif info.get("amount") is not None:
    amt=int(info["amount"])
   out.append({"type":typ,"source":info.get("source"),"destination":info.get("destination"),
    "mint":info.get("mint"),"amount":amt,"decimals":dec})
 return out

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"meteora_orca_exact_swap_instructions.json").read_text(encoding="utf-8"))
 rows=[]
 for x in src["rows"]:
  p=parent_index(x["level"],x["instruction_ordinal"])
  ts=transfers(x["transaction"],p)
  rows.append({"venue":x["venue"],"signature":x["signature"],"instruction_name":x["instruction_name"],
   "level":x["level"],"instruction_ordinal":x["instruction_ordinal"],"parent_instruction_index":p,
   "accounts":x["accounts"],"transfer_count":len(ts),"transfers":ts,"execution_authority":False})
 return {"revision":"USLS_070","row_count":len(rows),
  "venue_transfer_rows":{v:sum(x["venue"]==v and x["transfer_count"]>0 for x in rows) for v in sorted({x["venue"] for x in rows})},
  "rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_orca_instruction_transfer_evidence.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
