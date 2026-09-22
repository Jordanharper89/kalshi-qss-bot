from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_050_raydium_multifamily_swap_registry import PROGRAMS

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 router=json.loads((base/"multidex_live_event_router.json").read_text(encoding="utf-8"))
 ix=json.loads((base/"raydium_exact_swap_instructions.json").read_text(encoding="utf-8"))
 econ=json.loads((base/"raydium_exact_economic_swaps.json").read_text(encoding="utf-8"))
 matrix={}
 for v in PROGRAMS:
  activity=int(router["venue_row_counts"].get(v,0))
  swaps=sum(x["venue"]==v for x in ix["rows"])
  two=sum(x["venue"]==v and x["trader"] is not None for x in econ["rows"])
  oriented=sum(x["venue"]==v and x["decoder_state"]=="EXACT_QUOTE_ORIENTED_SWAP" for x in econ["rows"])
  if oriented>0:status="EXACT_QUOTE_ORIENTED_TRADE_DECODER_CERTIFIED"
  elif two>0:status="EXACT_SWAP_ECONOMICS_ORIENTATION_PENDING"
  elif swaps>0:status="EXACT_SWAP_INSTRUCTION_ECONOMICS_PENDING"
  elif activity>0:status="ACTIVITY_OBSERVED_DECODER_PENDING"
  else:status="NOT_OBSERVED_IN_SHORT_GATE"
  matrix[v]={"activity_rows":activity,"exact_swap_instructions":swaps,
   "exact_two_asset_swaps":two,"exact_quote_oriented_swaps":oriented,"status":status}
 certified=[v for v,x in matrix.items() if x["status"]=="EXACT_QUOTE_ORIENTED_TRADE_DECODER_CERTIFIED"]
 return {"revision":"USLS_054","matrix":matrix,"raydium_certified_venues":certified,
  "raydium_certified_count":len(certified),"phase4_status":"IN_PROGRESS",
  "next_boundary":"METEORA_ORCA_SHARED_DECODER_PLUGINS",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/raydium_multifamily_certification_matrix.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
