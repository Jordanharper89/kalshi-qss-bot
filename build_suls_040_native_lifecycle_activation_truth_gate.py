from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_040_native_lifecycle_activation_truth_gate.py"
TEST=ROOT/"test_suls_040_native_lifecycle_activation_truth_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 r=json.loads((b/"native_vault_balance_readback.json").read_text(encoding="utf-8"))
 n=json.loads((b/"native_lifecycle_snapshots.json").read_text(encoding="utf-8"))
 s=json.loads((b/"prospective_lifecycle_schedule.json").read_text(encoding="utf-8"))
 f=json.loads((b/"fresh_birth_lifecycle_admission.json").read_text(encoding="utf-8"))
 physical=bool(r.get("snapshot_count",0)>0 and n.get("snapshot_count",0)>0)
 schedule=bool(s.get("pending_count",0)>0)
 return {"revision":"SULS_040","physical_native_vault_readback":physical,
  "prospective_schedule_ready":schedule,"fresh_births_currently_admitted":int(f.get("fresh_birth_count",0)),
  "continuous_native_lifecycle_active":False,"profitable_edge_claimed":False,
  "next_required_boundary":"SULS_041_CONTINUOUS_NATIVE_BIRTH_AND_AGE_1S_5S_15S_WORKER",
  "execution_authority":False,"read_only":True,
  "scope":"Infrastructure ready; repeated prospective lifecycle outcomes not yet accumulated"}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_lifecycle_activation_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_040_native_lifecycle_activation_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["physical_native_vault_readback"] or not d["prospective_schedule_ready"]:
   self.fail("NATIVE_LIFECYCLE_FOUNDATION_NOT_READY")
  self.assertFalse(d["continuous_native_lifecycle_active"])
  self.assertFalse(d["profitable_edge_claimed"])
  print("[PASS] SULS-040 native lifecycle activation truth gate")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")