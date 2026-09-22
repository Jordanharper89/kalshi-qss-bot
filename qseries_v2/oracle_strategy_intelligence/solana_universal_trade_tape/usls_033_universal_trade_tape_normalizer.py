from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_030_universal_trade_tape_contract import validate
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_031_pump_exact_trade_discriminator_registry import PUMP

def normalize(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"pump_live_curve_trade_capture.json").read_text(encoding="utf-8"))
 rows=[]
 for n,x in enumerate(src.get("rows") or []):
  row={"trade_id":f'PUMP_FUN:{x["signature"]}:{x["instruction_index"]}:{n}',
   "signature":x["signature"],"slot":x.get("slot"),"block_time":x.get("block_time"),
   "observed_unix":x["observed_unix"],"venue":"PUMP_FUN","program_id":PUMP,
   "token_address":x["token_address"],"market_address":x["market_address"],
   "quote_mint":x["quote_mint"],"side":x["side"],"trader":None,
   "base_amount":None,"quote_amount":None,"effective_price":None,
   "birth_age_seconds":max(0.0,x["observed_unix"]-x["birth_observed_unix"]),
   "instruction_index":x["instruction_index"],
   "source_lineage":{"capture_revision":"USLS_032","discriminator_hex":x["discriminator_hex"],
    "instruction_name":x["instruction_name"]},
   "decoder_state":"SIDE_EXACT_AMOUNTS_PENDING","execution_authority":False}
  v=validate(row)
  if not v["valid"]:raise RuntimeError("INVALID_NORMALIZED_TRADE:"+json.dumps(v))
  rows.append(row)
 return {"revision":"USLS_033","row_count":len(rows),
  "buy_count":sum(1 for x in rows if x["side"]=="BUY"),
  "sell_count":sum(1 for x in rows if x["side"]=="SELL"),
  "amounts_pending_count":sum(1 for x in rows if x["base_amount"] is None or x["quote_amount"] is None),
  "rows":rows,"profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=normalize(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pump_normalized_trade_tape.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
