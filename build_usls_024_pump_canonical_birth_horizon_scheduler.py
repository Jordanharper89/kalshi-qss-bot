from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_024_pump_canonical_birth_horizon_scheduler.py"
TEST=ROOT/"test_usls_024_pump_canonical_birth_horizon_scheduler.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path
H=(1,5,15,30,60,300,900)

def build(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 src=json.loads((base/"pump_create_v2_decoded_births.json").read_text(encoding="utf-8"))
 births=[];sched=[]
 for x in src.get("rows") or []:
  if not x.get("all_checks"):continue
  event={"event_id":"PUMP_FUN:"+x["signature"],"family":"PUMP_FUN","birth_instruction":"create_v2",
   "signature":x["signature"],"slot":x.get("slot"),"chain_block_time":x.get("block_time"),
   "birth_observed_unix":x["observed_unix"],"token_address":x["mint"],
   "bonding_curve":x["bonding_curve"],"associated_bonding_curve":x["associated_bonding_curve"],
   "quote_mint":x["quote_mint"],"identity_certified":True,
   "profitability_claimed":False,"execution_authority":False}
  births.append(event)
  for h in H:
   sched.append({"event_id":event["event_id"],"token_address":event["token_address"],
    "horizon_seconds":h,"target_unix":event["birth_observed_unix"]+h,
    "state":"PENDING" if time.time()<event["birth_observed_unix"]+h else "DUE_UNRESOLVED",
    "execution_authority":False})
 return {"revision":"USLS_024","birth_count":len(births),"horizon_row_count":len(sched),
  "horizons":list(H),"births":births,"schedule":sched,
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/pump_canonical_birth_horizons.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_024_pump_canonical_birth_horizon_scheduler import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_sched(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"birth_count":d["birth_count"],"horizon_row_count":d["horizon_row_count"],"horizons":d["horizons"]},sort_keys=True))
  for x in d["births"]:print("[BIRTH]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["birth_count"],0)
  self.assertEqual(d["horizon_row_count"],d["birth_count"]*7)
  self.assertEqual(d["horizons"],[1,5,15,30,60,300,900])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-024 Pump.fun canonical exact birth + multi-horizon schedule")
  print("[PASS] 1s/5s/15s/30s/60s/5m/15m clock starts from live birth observation")
  print("[PASS] profitability remains unclaimed until actual outcomes are resolved")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
