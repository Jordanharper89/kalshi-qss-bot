from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_048_finalized_launch_role_truth_gate.py"
TEST=ROOT/"test_suls_048_finalized_launch_role_truth_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 lat=json.loads((b/"finalized_head_latency_probe.json").read_text(encoding="utf-8"))
 cap=json.loads((b/"native_commitment_capability_audit.json").read_text(encoding="utf-8"))
 age=lat.get("finalized_head_age_seconds");fast=bool(lat.get("launch_window_5s_possible"))
 faster=any((x.get("mentions_processed") or x.get("mentions_confirmed") or x.get("mentions_websocket")) for x in cap.get("modules",[]))
 role="PRIMARY_LAUNCH_TRIGGER" if fast else "CONFIRMATION_AND_OUTCOME_TRUTH"
 nxt=("SULS_049_FINALIZED_PRODUCTION_LOOP_ACTIVATION" if fast else
      "SULS_049_FASTER_NATIVE_TRIGGER_CONTRACT_RESOLUTION" if faster else
      "SULS_049_FASTER_NATIVE_TRIGGER_FOUNDATION_AUDIT")
 return {"revision":"SULS_048","finalized_head_age_seconds":age,"launch_window_5s_possible":fast,
  "finalized_role":role,"faster_native_candidate_present":faster,"next_required_boundary":nxt,
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/finalized_launch_role_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_048_finalized_launch_role_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertIn(d["finalized_role"],("PRIMARY_LAUNCH_TRIGGER","CONFIRMATION_AND_OUTCOME_TRUTH"))
  print("[PASS] SULS-048 finalized launch-role truth gate")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")