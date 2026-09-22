from __future__ import annotations
import json
from pathlib import Path

def reconcile(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"pump_trade_events_exact.json").read_text(encoding="utf-8"))
 rows=[]
 for x in src["rows"]:
  hits=[e for e in x["events"] if e["mint"]==x["token_address"] and e["side"]==x["expected_side"]]
  e=hits[0] if len(hits)==1 else None
  rows.append({"trade_id":x["trade_id"],"signature":x["signature"],
   "token_address":x["token_address"],"side":x["expected_side"],
   "event_match_count":len(hits),"trader":None if e is None else e["user"],
   "base_amount_raw":None if e is None else e["token_amount_raw"],
   "quote_amount_lamports":None if e is None else e["sol_amount_lamports"],
   "virtual_sol_reserves":None if e is None else e["virtual_sol_reserves"],
   "virtual_token_reserves":None if e is None else e["virtual_token_reserves"],
   "event_timestamp":None if e is None else e["timestamp"],
   "decoder_state":"TRADE_EVENT_EXACT" if e else "TRADE_EVENT_AMBIGUOUS_OR_MISSING",
   "execution_authority":False})
 return {"revision":"USLS_041","row_count":len(rows),
  "exact_count":sum(1 for x in rows if x["decoder_state"]=="TRADE_EVENT_EXACT"),
  "unresolved_count":sum(1 for x in rows if x["decoder_state"]!="TRADE_EVENT_EXACT"),
  "rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=reconcile(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pump_trade_event_reconciled.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
