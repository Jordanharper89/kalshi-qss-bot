from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_045b_universal_multidex_decoder_framework import PROGRAMS

def build(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_trade_tape"
 router=json.loads((base/"multidex_live_event_router.json").read_text(encoding="utf-8"))
 tape=json.loads((base/"multidex_universal_economic_tape.json").read_text(encoding="utf-8"))
 phase3=base/"phase3_pump_trade_tape_certification.json"
 pump_ok=False
 if phase3.exists():
  pump_ok=bool(json.loads(phase3.read_text(encoding="utf-8")).get("phase3_certified"))
 exact_by={}
 for x in tape["exact_rows"]:exact_by[x["venue"]]=exact_by.get(x["venue"],0)+1
 matrix={}
 for venue in PROGRAMS:
  activity=int(router["venue_row_counts"].get(venue,0));exact=int(exact_by.get(venue,0))
  if venue=="PUMP_FUN" and pump_ok:status="EXACT_TRADE_DECODER_CERTIFIED_UPSTREAM"
  elif exact>0:status="EXACT_TRADE_DECODER_CERTIFIED"
  elif activity>0:status="ACTIVITY_OBSERVED_DECODER_PENDING"
  else:status="NOT_OBSERVED_IN_SHORT_GATE"
  matrix[venue]={"program_id":PROGRAMS[venue],"activity_rows":activity,"exact_trade_rows":exact,"status":status}
 certified=[v for v,x in matrix.items() if x["status"].startswith("EXACT_TRADE_DECODER_CERTIFIED")]
 return {"revision":"USLS_049B","matrix":matrix,"certified_venues":certified,
  "certified_count":len(certified),"phase4_status":"IN_PROGRESS",
  "framework_certified":router["subscription_ack_count"]==14,
  "next_boundary":"ADD_RAYDIUM_METEORA_ORCA_DECODER_PLUGINS_TO_SHARED_FRAMEWORK",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/multidex_physical_certification_matrix.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
