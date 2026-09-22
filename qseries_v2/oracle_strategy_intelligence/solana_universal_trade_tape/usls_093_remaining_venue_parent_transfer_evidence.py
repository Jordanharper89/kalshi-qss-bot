from __future__ import annotations
import json
from pathlib import Path
def parent(level,ordinal):return int(str(level).split(":",1)[1]) if str(level).startswith("inner:") else int(ordinal)
def collect(tx,p):
 out=[]
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  if g.get("index")!=p:continue
  for ix in g.get("instructions") or []:
   q=ix.get("parsed")
   if not isinstance(q,dict):continue
   typ=q.get("type");info=q.get("info") or {}
   if typ in ("transfer","transferChecked","transferCheckedWithFee"):
    out.append({"kind":"TOKEN_TRANSFER","source":info.get("source"),"destination":info.get("destination"),
     "amount":info.get("amount"),"tokenAmount":info.get("tokenAmount"),"lamports":info.get("lamports")})
   elif info.get("lamports") is not None and info.get("source") and info.get("destination"):
    out.append({"kind":"SYSTEM_TRANSFER","source":info.get("source"),"destination":info.get("destination"),
     "amount":None,"tokenAmount":None,"lamports":info.get("lamports")})
 return out
def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((b/"remaining_venue_exact_account_roles.json").read_text(encoding="utf-8"));rows=[]
 for x in src["rows"]:
  ts=collect(x["transaction"],parent(x["level"],x["instruction_ordinal"]))
  rows.append({"venue":x["venue"],"signature":x["signature"],"instruction_name":x["instruction_name"],"side":x["side"],
   "roles":x["roles"],"transfer_count":len(ts),"transfers":ts,"execution_authority":False})
 return {"revision":"USLS_093","row_count":len(rows),
  "venue_transfer_rows":{v:sum(x["venue"]==v and x["transfer_count"]>0 for x in rows) for v in ("MOONIT","BOOP_FUN","HEAVEN")},
  "rows":rows,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/remaining_venue_parent_transfer_evidence.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
