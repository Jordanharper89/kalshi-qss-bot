from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_051_native_entry_trigger_truth_gate.py"
TEST=ROOT/"test_suls_051_native_entry_trigger_truth_gate.py"

MOD_TEXT=r'''from __future__ import annotations
import json
def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 p=json.loads((b/"native_commitment_latency_probe.json").read_text(encoding="utf-8"))
 confirmed=bool(p.get("confirmed_5s_possible"))
 processed=bool(p.get("processed_5s_possible"))
 if confirmed:
  role="CONFIRMED_PRIMARY_LAUNCH_TRIGGER"
  nxt="SULS_052_CONFIRMED_NATIVE_BIRTH_CAPTURE_ACTIVATION"
 elif processed:
  role="PROCESSED_EARLY_SIGNAL_WITH_CONFIRMATION"
  nxt="SULS_052_PROCESSED_TRIGGER_WITH_CONFIRMATION_LINEAGE"
 else:
  role="RPC_COMMITMENTS_TOO_SLOW"
  nxt="SULS_052_NATIVE_SUBSCRIPTION_TRIGGER_FOUNDATION"
 return {"revision":"SULS_051","trigger_role":role,
  "processed_5s_possible":processed,"confirmed_5s_possible":confirmed,
  "finalized_role":"CONFIRMATION_AND_OUTCOME_TRUTH",
  "next_required_boundary":nxt,
  "execution_authority":False,"read_only":True,
  "profitability_claimed":False}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_entry_trigger_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
'''

TEST_TEXT=r'''import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_051_native_entry_trigger_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertFalse(d["profitability_claimed"])
  print("[PASS] SULS-051 native entry-trigger truth gate")
if __name__=="__main__":unittest.main()
'''

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")