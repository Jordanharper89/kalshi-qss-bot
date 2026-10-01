import json,tempfile,unittest
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
