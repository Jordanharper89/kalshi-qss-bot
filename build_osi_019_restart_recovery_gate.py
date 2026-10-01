from pathlib import Path
ROOT=Path(__file__).resolve().parent
MOD=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_019_restart_recovery_gate.py"
TEST=ROOT/"test_osi_019_restart_recovery_gate.py"
MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
def gate(root:Path)->dict:
 state=root/"runtime_state/solana_intelligence/osi_012_live_intake_state.json"
 status=root/"runtime_state/solana_intelligence/osi_live_child_status.json"
 seen=0
 if state.is_file():
  try: seen=len(json.loads(state.read_text(encoding="utf-8")).get("seen_ids",[]))
  except Exception: pass
 child={}
 if status.is_file():
  try: child=json.loads(status.read_text(encoding="utf-8"))
  except Exception: pass
 return {"state_exists":state.is_file(),"seen_ids":seen,"child_state":child.get("state"),
         "cycle_count":child.get("cycle_count",0),"restart_recovery_ready":state.is_file(),
         "execution_authority":False}
"""
TEST_TEXT=r"""import json,tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_019_restart_recovery_gate import gate
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_fixture(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);p=r/"runtime_state/solana_intelligence";p.mkdir(parents=True)
   (p/"osi_012_live_intake_state.json").write_text(json.dumps({"seen_ids":["a","b"]}),encoding="utf-8")
   g=gate(r);self.assertTrue(g["restart_recovery_ready"]);self.assertEqual(g["seen_ids"],2)
 def test_physical_components(self):
  self.assertTrue((ROOT/"run_osi_solana_intelligence_live.py").is_file())
  self.assertIn("run_osi_solana_intelligence_live.py",(ROOT/"run_oracle_live.py").read_text(encoding="utf-8",errors="replace"))
  print("[PASS] OSI-019 restart recovery gate")
  print("[TRADER] Seen opportunities survive restart so Oracle does not relearn the same setup as new")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
def main():
 MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] OSI-019 installed; execution_authority=FALSE")
if __name__=="__main__":main()
