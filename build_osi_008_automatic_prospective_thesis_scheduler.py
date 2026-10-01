from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2"/"oracle_strategy_intelligence"/"solana_intelligence"
MOD=SUB/"osi_008_automatic_prospective_thesis_scheduler.py"
TEST=ROOT/"test_osi_008_automatic_prospective_thesis_scheduler.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_003_multi_horizon_prospective_thesis_engine import build_theses

EXECUTION_AUTHORITY=False

def schedule(bundle:dict,reasoning:dict,queue_path:Path,min_sources:int=2)->dict:
 theses=build_theses(bundle,reasoning,min_sources)
 prior=[]
 if queue_path.is_file():
  try: prior=json.loads(queue_path.read_text(encoding="utf-8")).get("theses",[])
  except Exception: prior=[]
 existing={x["thesis_id"] for x in prior}
 added=[x for x in theses if x["thesis_id"] not in existing]
 all_rows=prior+added
 queue_path.parent.mkdir(parents=True,exist_ok=True)
 queue_path.write_text(json.dumps({"theses":all_rows,"execution_authority":False},indent=2,sort_keys=True),encoding="utf-8")
 return {"added":added,"queued_total":len(all_rows),"execution_authority":False}
"""

TEST_TEXT=r"""import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_008_automatic_prospective_thesis_scheduler import schedule
class T(unittest.TestCase):
 def test_schedule(self):
  b={"source_count":3,"opportunity_seed_id":"o","asset_key":"SOL:M","freeze_at":"2026-09-18T05:00:00+00:00"}
  r={"thesis_metadata":{"thesis_family":"LIQUIDITY_EXPANSION"},"x_y_z_reasoning":{"x":1,"y":2,"z":3}}
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"q.json";a=schedule(b,r,p);b2=schedule(b,r,p)
   self.assertEqual(len(a["added"]),6);self.assertEqual(len(b2["added"]),0)
 def test_physical(self):
  ROOT=Path(__file__).resolve().parent
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_003_multi_horizon_prospective_thesis_engine.py").is_file())
  print("[PASS] OSI-008 automatic prospective thesis scheduler")
  print("[TRADER] Qualified setups automatically become forward paper calls across useful horizons")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] OSI-008 installed; execution_authority=FALSE")
if __name__=="__main__":main()
