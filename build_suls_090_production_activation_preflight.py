from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_090_production_activation_preflight.py"
TEST=ROOT/"test_suls_090_production_activation_preflight.py"

MOD_TEXT=r"""from __future__ import annotations
import json
def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 r=json.loads((b/"production_activation_readiness.json").read_text(encoding="utf-8"))
 t=json.loads((b/"top_level_osi_registration_gate.json").read_text(encoding="utf-8"))
 c=json.loads((b/"osi_child_binding_contract.json").read_text(encoding="utf-8"))
 ready=bool(r.get("production_activation_ready") and t.get("osi_registered_all")
  and t.get("no_direct_suls_registration") and c.get("syntax_ok") and c.get("execution_authority_false"))
 return {"revision":"SULS_090","preflight_ready":ready,
  "existing_osi_child_bound":bool(r.get("existing_osi_child_bound")),
  "top_level_osi_registered":bool(t.get("osi_registered_all")),
  "duplicate_suls_child":not bool(t.get("no_direct_suls_registration")),
  "production_24x7_active":False,"profitability_claimed":False,
  "next_required_boundary":"SULS_091_LIVE_RUNTIME_STATUS_CERTIFICATION",
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/production_activation_preflight.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_090_production_activation_preflight import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["preflight_ready"]:self.fail("PRODUCTION_ACTIVATION_PREFLIGHT_NOT_READY")
  self.assertFalse(d["duplicate_suls_child"]);self.assertFalse(d["profitability_claimed"])
  print("[PASS] SULS-090 production activation preflight")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*116);print(" SULS-090 PRODUCTION ACTIVATION PREFLIGHT");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()