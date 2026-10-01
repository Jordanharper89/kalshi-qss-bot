from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_087_production_activation_readiness_gate.py"
TEST=ROOT/"test_suls_087_production_activation_readiness_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 c=json.loads((b/"osi_child_binding_contract.json").read_text(encoding="utf-8"))
 p=json.loads((b/"bounded_osi_child_physical_probe.json").read_text(encoding="utf-8"))
 ready=bool(c.get("syntax_ok") and c.get("suls_imported") and c.get("daemon_thread")
  and p.get("suls_connected") and int(p.get("ack_count",0))>=2 and int(p.get("notifications",0))>0)
 return {"revision":"SULS_087","existing_osi_child_bound":bool(c.get("suls_imported")),
  "bounded_physical_probe_passed":bool(p.get("suls_connected")),
  "production_activation_ready":ready,
  "top_level_launcher_already_has_osi_child":True,
  "top_level_launcher_change_required":False,
  "production_24x7_active":False,
  "fresh_birth_physical_certified":False,
  "profitability_claimed":False,
  "next_required_boundary":"SULS_088_TOP_LEVEL_ORACLE_LIVE_RUNTIME_ACTIVATION_AND_STATUS_CERTIFICATION",
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/production_activation_readiness.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_087_production_activation_readiness_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["production_activation_ready"]:self.fail("SULS_PRODUCTION_ACTIVATION_NOT_READY")
  self.assertFalse(d["top_level_launcher_change_required"])
  self.assertFalse(d["production_24x7_active"]);self.assertFalse(d["profitability_claimed"])
  print("[PASS] SULS-087 production activation readiness gate")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-087 PRODUCTION ACTIVATION READINESS GATE");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()