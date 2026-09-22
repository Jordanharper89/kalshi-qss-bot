from __future__ import annotations
import json
from pathlib import Path

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 tape=json.loads((base/"pump_normalized_trade_tape.json").read_text(encoding="utf-8"))
 rec=json.loads((base/"pump_trade_event_reconciled.json").read_text(encoding="utf-8"))
 rb={x["trade_id"]:x for x in rec["rows"]};rows=[]
 for x in tape["rows"]:
  r=rb.get(x["trade_id"],{});raw_base=r.get("base_amount_raw");lam=r.get("quote_amount_lamports")
  y=dict(x);y["trader"]=r.get("trader")
  y["base_amount_raw"]=raw_base;y["base_decimals"]=6
  y["base_amount"]=None if raw_base is None else raw_base/1_000_000
  y["quote_amount_lamports"]=lam
  y["quote_amount"]=None if lam is None else lam/1_000_000_000
  y["effective_price"]=None if not y["base_amount"] or y["quote_amount"] is None else y["quote_amount"]/y["base_amount"]
  y["virtual_sol_reserves_after"]=r.get("virtual_sol_reserves")
  y["virtual_token_reserves_after"]=r.get("virtual_token_reserves")
  y["decoder_state"]="TRADE_EVENT_ECONOMICS_EXACT" if y["effective_price"] is not None else "TRADE_EVENT_UNRESOLVED"
  y["source_lineage"]={**(y.get("source_lineage") or {}),"economic_decoder_revision":"USLS_042"}
  rows.append(y)
 return {"revision":"USLS_042","row_count":len(rows),
  "economic_exact_count":sum(1 for x in rows if x["decoder_state"]=="TRADE_EVENT_ECONOMICS_EXACT"),
  "rows":rows,"profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pump_exact_economic_trade_tape.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
