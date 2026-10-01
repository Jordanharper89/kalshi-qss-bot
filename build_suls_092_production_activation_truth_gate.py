from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_092_production_activation_truth_gate.py"
TEST=ROOT/"test_suls_092_production_activation_truth_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json

def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 pre=json.loads((b/"production_activation_preflight.json").read_text(encoding="utf-8"))
 live=json.loads((b/"live_runtime_status_certification.json").read_text(encoding="utf-8"))
 ready=bool(pre.get("preflight_ready") and live.get("production_24x7_active"))
 return {"revision":"SULS_092",
  "production_preflight_ready":bool(pre.get("preflight_ready")),
  "production_24x7_active":bool(live.get("production_24x7_active")),
  "event_driven_solana_birth_surveillance_active":ready,
  "fresh_birth_physical_certified":False,
  "profitability_learning_ready":False,
  "profitability_claimed":False,
  "next_required_boundary":"SULS_093_FRESH_BIRTH_PHYSICAL_CAPTURE_AND_LIFECYCLE_CERTIFICATION",
  "execution_authority":False,"read_only":True}

def write(root):
 d=gate(root)
 p=root/"runtime_state/solana_opportunities/launch_surveillance/production_activation_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_092_production_activation_truth_gate import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["event_driven_solana_birth_surveillance_active"]:
   self.fail("SULS_PRODUCTION_NOT_ACTIVE")
  self.assertTrue(d["production_24x7_active"])
  self.assertFalse(d["fresh_birth_physical_certified"])
  self.assertFalse(d["profitability_learning_ready"])
  self.assertFalse(d["profitability_claimed"])
  print("[PASS] SULS-092 production activation truth gate")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
"""

def main():
 print("="*116)
 print(" SULS-092 PRODUCTION ACTIVATION TRUTH GATE")
 print("="*116)
 SUB.mkdir(parents=True,exist_ok=True)
 MOD.write_text(MOD_TEXT,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT))
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 main()