from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_061_confirmed_fast_lane_truth_gate.py"
TEST=ROOT/"test_suls_061_confirmed_fast_lane_truth_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 lat=json.loads((b/"confirmed_end_to_end_latency_gate.json").read_text(encoding="utf-8"))
 st=json.loads((b/"incremental_confirmed_head_state.json").read_text(encoding="utf-8"))
 evp=b/"confirmed_tradeable_birth_events.json";qp=b/"confirmed_fresh_birth_horizon_queue.json"
 ev=json.loads(evp.read_text(encoding="utf-8")) if evp.exists() else {"event_count":0}
 q=json.loads(qp.read_text(encoding="utf-8")) if qp.exists() else {"pending_count":0,"admitted_fresh_births":0}
 foundation=bool(lat.get("worker_cycle_under_5s") and st.get("last_cycle_unix"))
 fresh=int(q.get("admitted_fresh_births",0))
 return {"revision":"SULS_061","confirmed_fast_lane_worker_ready":foundation,
  "worker_cycle_under_5s":bool(lat.get("worker_cycle_under_5s")),
  "tradeable_birth_events":int(ev.get("event_count",0)),
  "fresh_births_admitted":fresh,"pending_horizon_checks":int(q.get("pending_count",0)),
  "continuous_runtime_active":False,"fresh_birth_physical_certified":fresh>0,
  "profitability_learning_ready":False,
  "next_required_boundary":"SULS_062_CONFIRMED_FAST_LANE_RUNTIME_ACTIVATION_AND_FRESH_BIRTH_CAPTURE",
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/confirmed_fast_lane_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_061_confirmed_fast_lane_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["confirmed_fast_lane_worker_ready"]:self.fail("CONFIRMED_FAST_LANE_WORKER_NOT_READY")
  self.assertFalse(d["continuous_runtime_active"]);self.assertFalse(d["profitability_learning_ready"])
  print("[PASS] SULS-061 confirmed fast-lane truth gate")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")