from __future__ import annotations
import json
from pathlib import Path

def add(rows,venue,src,revision):
 for n,x in enumerate(src):
  e=x.get("economics") or x
  im=e.get("input_mint");om=e.get("output_mint");ia=e.get("input_amount");oa=e.get("output_amount")
  if not (im and om and ia is not None and oa is not None):continue
  rows.append({"trade_id":f'{venue}:{x["signature"]}:{n}',"signature":x["signature"],"venue":venue,
   "market_address":x.get("pool"),"trader":x.get("trader"),"input_mint":im,"input_amount":ia,
   "output_mint":om,"output_amount":oa,"effective_output_per_input":oa/ia if ia else None,
   "side":"UNKNOWN_TRADE_TYPE","decoder_state":"EXACT_ECONOMIC_TRADE",
   "source_lineage":{"economics_revision":revision},"execution_authority":False})

def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape";rows=[]
 dbc=json.loads((b/"meteora_dbc_exact_economics.json").read_text(encoding="utf-8"))
 rec=json.loads((b/"meteora_orca_exact_transfer_reconciliation.json").read_text(encoding="utf-8"))
 v1=json.loads((b/"meteora_damm_v1_strict_economics.json").read_text(encoding="utf-8"))
 orca=json.loads((b/"orca_exact_mint_decimal_economics.json").read_text(encoding="utf-8"))
 add(rows,"METEORA_DBC",dbc["rows"],"USLS_081")
 add(rows,"METEORA_DAMM_V2",[x for x in rec["rows"] if x["venue"]=="METEORA_DAMM"],"USLS_072")
 add(rows,"METEORA_DLMM",[x for x in rec["rows"] if x["venue"]=="METEORA_DLMM"],"USLS_072")
 add(rows,"METEORA_DAMM_V1",v1["rows"],"USLS_082B")
 add(rows,"ORCA",orca["rows"],"USLS_083B")
 counts={v:sum(x["venue"]==v for x in rows) for v in ("METEORA_DBC","METEORA_DAMM_V2","METEORA_DLMM","METEORA_DAMM_V1","ORCA")}
 return {"revision":"USLS_084","exact_trade_count":len(rows),"venue_counts":counts,"rows":rows,
  "orientation_policy":"INPUT_OUTPUT_NATIVE_NO_FORCED_QUOTE_SIDE","profitability_claimed":False,
  "execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_orca_universal_trade_rows.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
