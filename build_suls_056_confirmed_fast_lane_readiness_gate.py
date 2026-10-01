from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_056_confirmed_fast_lane_readiness_gate.py"
TEST=ROOT/"test_suls_056_confirmed_fast_lane_readiness_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 cap=json.loads((b/"confirmed_native_block_capture.json").read_text(encoding="utf-8"))
 env=json.loads((b/"confirmed_transaction_envelope_bridge.json").read_text(encoding="utf-8"))
 det=json.loads((b/"confirmed_meteora_birth_detector.json").read_text(encoding="utf-8"))
 foundation=bool(cap.get("confirmed_capture_ready") and env.get("transaction_count",0)>0)
 fresh=sum(1 for x in det.get("births",[]) if x.get("age_seconds") is not None and x["age_seconds"]<=5.0)
 return {"revision":"SULS_056","confirmed_fast_lane_foundation_ready":foundation,
  "fresh_confirmed_births_observed":fresh,"confirmed_births_observed":det.get("birth_count",0),
  "continuous_confirmed_birth_worker_active":False,"profitability_learning_ready":False,
  "next_required_boundary":"SULS_057_CONTINUOUS_CONFIRMED_FAST_LANE_AND_FRESH_BIRTH_CERTIFICATION",
  "execution_authority":False,"read_only":True,
  "scope":"Confirmed fast-lane components physically proven; continuous fresh birth capture still unclaimed"}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/confirmed_fast_lane_readiness.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_056_confirmed_fast_lane_readiness_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["confirmed_fast_lane_foundation_ready"]:self.fail("CONFIRMED_FAST_LANE_FOUNDATION_NOT_READY")
  self.assertFalse(d["continuous_confirmed_birth_worker_active"])
  self.assertFalse(d["profitability_learning_ready"])
  print("[PASS] SULS-056 confirmed fast-lane readiness gate")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")