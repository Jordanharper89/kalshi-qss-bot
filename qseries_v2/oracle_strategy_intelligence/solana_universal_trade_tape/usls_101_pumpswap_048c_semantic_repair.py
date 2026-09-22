from __future__ import annotations
import json
from pathlib import Path

PROGRAM="pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"

def load(p):
 try:return json.loads(p.read_text(encoding="utf-8"))
 except Exception:return None

def rows_of(d):
 if isinstance(d,dict):
  for k in ("rows","trades","events"):
   if isinstance(d.get(k),list):return d[k]
 return []

def source(root):
 audit=load(Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pumpswap_048c_source_audit.json")
 if not audit or not audit.get("candidates"):raise RuntimeError("USLS_100_AUDIT_REQUIRED")
 ranked=audit["candidates"]
 preferred=[x for x in ranked if x.get("exact_like_count")==117] or ranked
 for c in preferred:
  p=Path(root)/c["path"];d=load(p);rs=[x for x in rows_of(d) if x.get("venue")=="PUMP_SWAP" or x.get("program_id")==PROGRAM]
  if rs:return p,d,rs
 raise RuntimeError("NO_PUMPSWAP_ROWS")

def true_block_time(x):
 for k in ("transaction_block_time","tx_block_time"):
  if x.get(k) is not None:return x[k]
 t=x.get("transaction")
 if isinstance(t,dict) and t.get("blockTime") is not None:return t["blockTime"]
 return None

def repair_row(x):
 y=dict(x)
 old_block=y.get("block_time")
 if "instruction_index" in y and "log_index" not in y:
  y["log_index"]=y.get("instruction_index")
 y["instruction_index"]=None
 y["event_observed_unix"]=y.get("observed_unix",old_block)
 y["block_time"]=true_block_time(y)
 sl=dict(y.get("source_lineage") or {})
 sl["identity_revision"]="USLS_047C";sl["semantic_repair_revision"]="USLS_101"
 sl["instruction_position_policy"]="LOG_INDEX_PRESERVED_IN_LOG_INDEX_INSTRUCTION_INDEX_UNCLAIMED"
 sl["time_policy"]="EVENT_OBSERVED_UNIX_SEPARATE_FROM_TRANSACTION_BLOCK_TIME"
 y["source_lineage"]=sl
 y["execution_authority"]=False
 return y

def build(root):
 p,d,rs=source(root);rows=[repair_row(x) for x in rs]
 return {"revision":"USLS_101","semantic_contract":"PUMPSWAP_048C","source_path":str(p.relative_to(root)),
  "row_count":len(rows),"exact_trade_count":sum(str(x.get("decoder_state","")).startswith("EXACT") for x in rows),
  "rows":rows,"repairs":{"instruction_index_semantics":True,"event_vs_block_time_separation":True,"identity_revision_047c":True},
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pumpswap_048c_repaired_trades.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
