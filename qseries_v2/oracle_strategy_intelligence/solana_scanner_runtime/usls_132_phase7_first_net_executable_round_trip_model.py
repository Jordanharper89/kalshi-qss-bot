from __future__ import annotations
import json
from pathlib import Path
SRC="runtime_state/solana_opportunities/solana_scanner/phase7_first_strict_executable_ready_rows.json"

def run(root):
 d=json.loads((Path(root)/SRC).read_text(encoding="utf-8"))
 groups={}
 for x in d.get("ready_rows",[]):
  groups.setdefault(x.get("market_address"),[]).append(x)
 trips=[]
 for market,xs in groups.items():
  xs.sort(key=lambda x:(x.get("observation_latency_seconds") or 0,str(x.get("trade_signature"))))
  # Preserve source order from parent rows where possible.
  parent=[x for x in d.get("rows",[]) if x.get("market_address")==market and x.get("executable_ready")]
  if parent:xs=parent
  for a,b in zip(xs,xs[1:]):
   p0=float(a["effective_price"]);p1=float(b["effective_price"])
   gross=(p1/p0)-1
   fees=float(a["fee_fraction"])+float(b["fee_fraction"])
   dev=abs(float(a["realized_execution_deviation_fraction"]))+abs(float(b["realized_execution_deviation_fraction"]))
   net=gross-fees-dev
   trips.append({"family":"PUMP_SWAP","market_address":market,
    "entry_signature":a["trade_signature"],"exit_signature":b["trade_signature"],
    "entry_executable_observed_price":p0,"exit_executable_observed_price":p1,
    "gross_return":gross,"round_trip_fee_fraction":fees,
    "round_trip_execution_deviation_fraction":dev,
    "conservative_net_return_after_explicit_fee_and_execution_deviation":net,
    "execution_authority":False})
 return {"revision":"USLS_132","round_trip_count":len(trips),"round_trips":trips,
  "net_semantics":"CONSERVATIVE_RESEARCH_MODEL_OBSERVED_EXECUTION_PRICES_MINUS_EXPLICIT_FEES_MINUS_ABSOLUTE_EXECUTION_DEVIATION",
  "phase7_status":"IN_PROGRESS",
  "remaining_required_capability":"EXPAND_STRICT_EXECUTABLE_FRICTION_MODELS_ACROSS_ALL_CERTIFIED_VENUES_AND_VALIDATE_PROSPECTIVELY",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_first_net_executable_round_trip_model.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
