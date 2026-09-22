from __future__ import annotations
import json
from pathlib import Path

REQUIRED=("trade_id","signature","slot","block_time","observed_unix","venue","program_id",
"token_address","market_address","quote_mint","side","trader","base_amount","quote_amount",
"effective_price","birth_age_seconds","instruction_index","source_lineage","decoder_state",
"execution_authority")

SIDES=("BUY","SELL","UNKNOWN_TRADE_TYPE")

def validate(row):
 missing=[k for k in REQUIRED if k not in row]
 errors=[]
 if row.get("side") not in SIDES:errors.append("INVALID_SIDE")
 if row.get("execution_authority") is not False:errors.append("EXECUTION_AUTHORITY_NOT_FALSE")
 if not row.get("trade_id"):errors.append("MISSING_TRADE_ID")
 return {"valid":not missing and not errors,"missing":missing,"errors":errors}

def contract():
 return {"revision":"USLS_030","schema_version":1,"required_fields":list(REQUIRED),
  "allowed_sides":list(SIDES),"unknown_retention":True,"append_only":True,
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 root=Path(root);p=root/"runtime_state/solana_opportunities/universal_trade_tape"
 p.mkdir(parents=True,exist_ok=True)
 q=p/"trade_tape_contract.json";d=contract()
 q.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return q,d
