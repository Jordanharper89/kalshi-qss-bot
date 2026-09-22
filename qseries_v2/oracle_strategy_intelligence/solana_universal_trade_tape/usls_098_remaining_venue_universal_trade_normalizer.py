from __future__ import annotations
import json
from pathlib import Path
def add(rows,venue,src,revision):
 for n,x in enumerate(src):
  if not x["decoder_state"].startswith("EXACT_"):continue
  rows.append({"trade_id":f'{venue}:{x["signature"]}:{n}',"signature":x["signature"],"venue":venue,
   "market_address":x["market_address"],"trader":x["trader"],"side":x["side"],
   "input_asset":x["input_asset"],"input_amount":x["input_amount"],
   "output_asset":x["output_asset"],"output_amount":x["output_amount"],
   "effective_output_per_input":x["output_amount"]/x["input_amount"],
   "decoder_state":"EXACT_ECONOMIC_TRADE","source_lineage":{"economics_revision":revision},
   "execution_authority":False})
def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape";rows=[]
 m=json.loads((b/"moonit_exact_economics.json").read_text(encoding="utf-8"))
 o=json.loads((b/"boop_exact_economics.json").read_text(encoding="utf-8"))
 h=json.loads((b/"heaven_exact_economics.json").read_text(encoding="utf-8"))
 add(rows,"MOONIT",m["rows"],"USLS_095");add(rows,"BOOP_FUN",o["rows"],"USLS_096");add(rows,"HEAVEN",h["rows"],"USLS_097")
 counts={v:sum(x["venue"]==v for x in rows) for v in ("MOONIT","BOOP_FUN","HEAVEN")}
 return {"revision":"USLS_098","exact_trade_count":len(rows),"venue_counts":counts,"rows":rows,
  "native_sol_policy":"NATIVE_SOL_PSEUDO_ASSET_NOT_FALSE_WS0L_MINT",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/remaining_venue_universal_trade_rows.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
