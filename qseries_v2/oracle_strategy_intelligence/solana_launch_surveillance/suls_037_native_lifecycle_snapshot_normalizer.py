from __future__ import annotations
import json
from decimal import Decimal
def D(x):
 try:return Decimal(str(x))
 except Exception:return None
def run(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 raw=json.loads((b/"native_vault_balance_readback.json").read_text(encoding="utf-8"))
 birth=json.loads((b/"canonical_tradeable_native_birth_events.json").read_text(encoding="utf-8"))
 bm={x["event_id"]:x for x in birth.get("events",[])};rows=[]
 for x in raw.get("snapshots",[]):
  e=bm.get(x["event_id"]) or {};ta=D(x["token"].get("ui_amount_string"));qa=D(x["quote"].get("ui_amount_string"))
  ratio=(qa/ta) if ta and qa and ta!=0 else None
  bta=D(e.get("initial_token_amount"));bqa=D(e.get("initial_quote_amount"))
  br=(bqa/bta) if bta and bqa and bta!=0 else None
  ret=((ratio/br)-1) if ratio is not None and br not in (None,0) else None
  rows.append({"event_id":x["event_id"],"signature":x["signature"],"age_seconds":x["age_seconds"],
   "token_reserve":None if ta is None else str(ta),"quote_reserve":None if qa is None else str(qa),
   "quote_per_token":None if ratio is None else str(ratio),
   "return_from_birth":None if ret is None else str(ret),"execution_authority":False})
 return {"revision":"SULS_037","snapshot_count":len(rows),"snapshots":rows,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_lifecycle_snapshots.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
