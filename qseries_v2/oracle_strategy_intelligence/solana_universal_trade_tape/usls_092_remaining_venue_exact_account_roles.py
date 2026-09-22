from __future__ import annotations
import json
from pathlib import Path
def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((b/"remaining_venue_exact_trade_census.json").read_text(encoding="utf-8"));rows=[]
 for x in src["rows"]:
  roles={k:(x["accounts"][i] if i<len(x["accounts"]) else None) for i,k in enumerate(x["role_names"])}
  ok=all(roles.values())
  rows.append({"venue":x["venue"],"signature":x["signature"],"level":x["level"],"instruction_ordinal":x["instruction_ordinal"],
   "instruction_name":x["instruction_name"],"side":x["side"],"roles":roles,
   "role_state":"SOURCE_LAYOUT_EXACT" if ok else "ACCOUNT_ROLE_INCOMPLETE","transaction":x["transaction"],"execution_authority":False})
 return {"revision":"USLS_092","row_count":len(rows),"exact_role_count":sum(x["role_state"]=="SOURCE_LAYOUT_EXACT" for x in rows),
  "venue_exact_role_counts":{v:sum(x["venue"]==v and x["role_state"]=="SOURCE_LAYOUT_EXACT" for x in rows) for v in ("MOONIT","BOOP_FUN","HEAVEN")},
  "rows":rows,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/remaining_venue_exact_account_roles.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
