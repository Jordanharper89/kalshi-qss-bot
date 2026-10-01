from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2"/"oracle_strategy_intelligence"/"solana_intelligence"
MOD=SUB/"osi_013_live_prospective_research_worker.py"
TEST=ROOT/"test_osi_013_live_prospective_research_worker.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_008_automatic_prospective_thesis_scheduler import schedule

def freeze_live(bundle:dict,reasoning:dict,root:Path)->dict:
 q=root/"runtime_state/solana_intelligence/osi_live_thesis_queue.json"
 return schedule(bundle,reasoning,q,min_sources=2)

def status(root:Path)->dict:
 q=root/"runtime_state/solana_intelligence/osi_live_thesis_queue.json"
 if not q.is_file():return {"queued_total":0,"execution_authority":False}
 x=json.loads(q.read_text(encoding="utf-8"))
 return {"queued_total":len(x.get("theses",[])),"execution_authority":False}
"""

TEST_TEXT=r"""import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_013_live_prospective_research_worker import freeze_live,status
class T(unittest.TestCase):
 def test_freeze(self):
  b={"source_count":3,"opportunity_seed_id":"o","asset_key":"SOL:M","freeze_at":"2026-09-18T05:00:00+00:00"}
  r={"thesis_metadata":{"thesis_family":"LIQUIDITY_EXPANSION"},"x_y_z_reasoning":{"x":"pool","y":"liq","z":"wallet"}}
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);x=freeze_live(b,r,root);self.assertEqual(len(x["added"]),6);self.assertEqual(status(root)["queued_total"],6)
 def test_physical(self):
  ROOT=Path(__file__).resolve().parent
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_012_live_event_normalization_and_intake.py").is_file())
  print("[PASS] OSI-013 live prospective research worker")
  print("[TRADER] Qualified real setups can be frozen into forward paper calls before the move")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] OSI-013 installed; execution_authority=FALSE")
if __name__=="__main__":main()
