from __future__ import annotations
import json
from pathlib import Path

def enrich(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_trade_tape"
 tape=json.loads((base/"pump_normalized_trade_tape.json").read_text(encoding="utf-8"))
 part=json.loads((base/"pump_trade_participants_amounts.json").read_text(encoding="utf-8"))
 quote=json.loads((base/"pump_quote_amount_evidence.json").read_text(encoding="utf-8"))
 pb={x["trade_id"]:x for x in part["rows"]};qb={x["trade_id"]:x for x in quote["rows"]}
 rows=[]
 for x in tape["rows"]:
  p=pb.get(x["trade_id"],{});q=qb.get(x["trade_id"],{})
  y=dict(x);y["trader"]=p.get("trader");y["base_amount"]=p.get("base_amount")
  y["quote_amount"]=q.get("quote_amount")
  y["effective_price"]=(y["quote_amount"]/y["base_amount"]) if y["quote_amount"] and y["base_amount"] else None
  y["decoder_state"]=("FULL_TRADE_AMOUNTS_EXACT" if y["effective_price"] is not None else
   "SIDE_TRADER_BASE_EXACT_QUOTE_PENDING" if y["trader"] and y["base_amount"] else
   "SIDE_EXACT_PARTICIPANT_OR_AMOUNT_PENDING")
  y["source_lineage"]={**(y.get("source_lineage") or {}),
   "participant_amount_revision":"USLS_036","quote_evidence_revision":"USLS_037"}
  rows.append(y)
 return {"revision":"USLS_038","row_count":len(rows),
  "trader_base_exact_count":sum(1 for x in rows if x["trader"] and x["base_amount"]),
  "full_amount_exact_count":sum(1 for x in rows if x["effective_price"] is not None),
  "rows":rows,"profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=enrich(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pump_enriched_trade_tape.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
