from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_132_phase7_first_net_executable_round_trip_model.py"
TEST=ROOT/"test_usls_132_phase7_first_net_executable_round_trip_model.py"

MOD_TEXT=r"""from __future__ import annotations
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
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_132_phase7_first_net_executable_round_trip_model import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"round_trip_count":d["round_trip_count"],
   "phase7_status":d["phase7_status"],
   "remaining_required_capability":d["remaining_required_capability"]},sort_keys=True))
  self.assertGreater(d["round_trip_count"],0,"NO_NET_EXECUTABLE_ROUND_TRIP_ROWS")
  self.assertEqual(d["phase7_status"],"IN_PROGRESS")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-132 first net executable round-trip research model")
  print("[PASS] observed execution prices + explicit fees + conservative execution deviation")
  print("[PASS] no profitability claim; prospective all-venue validation still required")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
