from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_022_live_pump_create_v2_capture import _tx

def hydrate(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"pump_normalized_trade_tape.json").read_text(encoding="utf-8"))
 rows=[];cache={}
 for x in src.get("rows") or []:
  sig=x["signature"]
  if sig not in cache:
   cache[sig]=_tx(sig)
   time.sleep(.08)
  tx=cache[sig]
  rows.append({"trade_id":x["trade_id"],"signature":sig,"side":x["side"],
   "token_address":x["token_address"],"market_address":x["market_address"],
   "quote_mint":x["quote_mint"],"birth_age_seconds":x["birth_age_seconds"],
   "instruction_index":x["instruction_index"],"raw_transaction":tx,
   "hydrated":tx is not None,"execution_authority":False})
 return {"revision":"USLS_035","row_count":len(rows),
  "hydrated_count":sum(1 for x in rows if x["hydrated"]),
  "unique_signature_count":len(cache),"rows":rows,
  "execution_authority":False,"read_only":True}

def write(root):
 d=hydrate(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pump_trade_raw_transactions.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
